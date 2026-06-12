from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

from backend.utils.numpy_compat import apply_numpy_compat

apply_numpy_compat()
import numpy as np
import pandas as pd
from sklearn.ensemble import (
    ExtraTreesClassifier,
    HistGradientBoostingClassifier,
    RandomForestClassifier,
)
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, confusion_matrix, roc_auc_score
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

try:
    from xgboost import XGBClassifier
except Exception:  # pragma: no cover - optional dependency fallback
    XGBClassifier = None

try:
    from lightgbm import LGBMClassifier
except Exception:  # pragma: no cover - optional dependency fallback
    LGBMClassifier = None


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add compact process-stage aggregates and missingness signals."""
    out = df.copy()
    new_cols: Dict[str, pd.Series] = {}
    x_cols = [c for c in out.columns if c.startswith("X")]

    for col in x_cols:
        new_cols[f"{col}_missing"] = out[col].isna().astype(int)

    groups = {
        "g_temp": [f"X{i}" for i in range(1, 10)],
        "g_10_16": [f"X{i}" for i in range(10, 17)],
        "g_17_22": [f"X{i}" for i in range(17, 23)],
        "g_23_33": [f"X{i}" for i in range(23, 34)],
        "g_34_40": [f"X{i}" for i in range(34, 41)],
        "g_41_49": [f"X{i}" for i in range(41, 50)],
    }
    for name, cols in groups.items():
        arr = out[cols]
        new_cols[f"{name}_mean"] = arr.mean(axis=1)
        new_cols[f"{name}_std"] = arr.std(axis=1)
        new_cols[f"{name}_min"] = arr.min(axis=1)
        new_cols[f"{name}_max"] = arr.max(axis=1)
        new_cols[f"{name}_range"] = new_cols[f"{name}_max"] - new_cols[f"{name}_min"]
        new_cols[f"{name}_zeros"] = (arr.fillna(999999) == 0).sum(axis=1)

    pairs = [
        ("X13", "X35"),
        ("X13", "X36"),
        ("X35", "X36"),
        ("X34", "X35"),
        ("X36", "X37"),
        ("X10", "X30"),
        ("X30", "X33"),
        ("X4", "X7"),
        ("X5", "X8"),
        ("X41", "X43"),
        ("X45", "X49"),
    ]
    for a, b in pairs:
        new_cols[f"{a}_minus_{b}"] = out[a] - out[b]
        new_cols[f"{a}_div_{b}"] = out[a] / out[b].replace(0, np.nan)

    return pd.concat([out, pd.DataFrame(new_cols, index=out.index)], axis=1)


def build_models(y: np.ndarray) -> Dict[str, object]:
    scale_pos_weight = (len(y) - y.sum()) / y.sum()
    models: Dict[str, object] = {
        "extra": make_pipeline(
            SimpleImputer(strategy="median"),
            ExtraTreesClassifier(
                n_estimators=1200,
                class_weight="balanced",
                min_samples_leaf=1,
                max_features="sqrt",
                random_state=1,
                n_jobs=-1,
            ),
        ),
        "rf": make_pipeline(
            SimpleImputer(strategy="median"),
            RandomForestClassifier(
                n_estimators=1000,
                class_weight="balanced_subsample",
                min_samples_leaf=1,
                max_features="sqrt",
                random_state=2,
                n_jobs=-1,
            ),
        ),
        "hgb": make_pipeline(
            SimpleImputer(strategy="median"),
            HistGradientBoostingClassifier(
                random_state=3,
                learning_rate=0.025,
                max_iter=500,
                max_leaf_nodes=8,
                l2_regularization=0.2,
                class_weight="balanced",
            ),
        ),
        "log": make_pipeline(
            SimpleImputer(strategy="median"),
            StandardScaler(),
            LogisticRegression(class_weight="balanced", max_iter=5000, C=0.08),
        ),
    }
    if XGBClassifier is not None:
        models["xgb"] = make_pipeline(
            SimpleImputer(strategy="median"),
            XGBClassifier(
                n_estimators=500,
                max_depth=2,
                learning_rate=0.025,
                subsample=0.85,
                colsample_bytree=0.75,
                reg_lambda=4,
                reg_alpha=0.2,
                scale_pos_weight=scale_pos_weight,
                eval_metric="logloss",
                random_state=4,
                n_jobs=-1,
            ),
        )
    if LGBMClassifier is not None:
        models["lgb"] = make_pipeline(
            SimpleImputer(strategy="median"),
            LGBMClassifier(
                n_estimators=500,
                max_depth=3,
                learning_rate=0.025,
                num_leaves=7,
                min_child_samples=12,
                subsample=0.85,
                colsample_bytree=0.75,
                reg_lambda=4,
                scale_pos_weight=scale_pos_weight,
                random_state=5,
                n_jobs=-1,
                verbose=-1,
            ),
        )
    return models


def summarize_predictions(y: np.ndarray, prob: np.ndarray, top_ks: Iterable[int]) -> List[str]:
    lines = [
        f"auc={roc_auc_score(y, prob):.4f} ap={average_precision_score(y, prob):.4f}"
    ]
    for k in top_ks:
        threshold = np.sort(prob)[-k]
        pred = (prob >= threshold).astype(int)
        tn, fp, fn, tp = confusion_matrix(y, pred).ravel()
        recall = tp / (tp + fn)
        precision = tp / (tp + fp) if tp + fp else 0
        lines.append(
            f"top{k}: tp={tp} fp={fp} fn={fn} "
            f"recall={recall:.3f} precision={precision:.3f}"
        )
    return lines


def write_submission(test_ids: pd.Series, probs: np.ndarray, out_file: Path, top_k: int) -> None:
    submission = pd.DataFrame({"CoilID": test_ids.to_numpy()})
    threshold = np.sort(probs)[-top_k]
    submission["Y"] = (probs >= threshold).astype(int)
    submission.to_csv(out_file, index=False)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", required=True, type=Path)
    parser.add_argument("--out-dir", default=Path("outputs"), type=Path)
    args = parser.parse_args()

    train = pd.read_csv(args.data_dir / "train.csv")
    test = pd.read_csv(args.data_dir / "test.csv")
    sample = pd.read_csv(args.data_dir / "sample_submission.csv")

    y = train["Y"].astype(int).to_numpy()
    x_train = add_features(train.drop(columns=["Y"]))
    x_test = add_features(test)
    models = build_models(y)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    cv = StratifiedKFold(n_splits=7, shuffle=True, random_state=42)
    report: List[str] = [
        f"train_shape={train.shape} test_shape={test.shape}",
        f"train_positive_rate={y.mean():.4f} train_positives={int(y.sum())}",
        "",
    ]

    cv_probs = []
    test_probs = []
    for name, model in models.items():
        prob = cross_val_predict(model, x_train, y, cv=cv, method="predict_proba")[:, 1]
        cv_probs.append(prob)
        report.append(f"[{name}]")
        report.extend(summarize_predictions(y, prob, top_ks=[10, 17, 30, 50, 100]))
        report.append("")

        model.fit(x_train, y)
        test_prob = model.predict_proba(x_test)[:, 1]
        test_probs.append(test_prob)

    ensemble_cv = np.mean(np.vstack(cv_probs), axis=0)
    ensemble_test = np.mean(np.vstack(test_probs), axis=0)
    report.append("[ensemble_mean]")
    report.extend(summarize_predictions(y, ensemble_cv, top_ks=[10, 17, 30, 50, 100, 150]))
    report.append("")

    ranked = test[["CoilID"]].copy()
    ranked["ensemble_probability"] = ensemble_test
    ranked = ranked.sort_values("ensemble_probability", ascending=False)
    report.append("Top ranked test coils")
    report.append(ranked.head(80).to_string(index=False))

    for k in [10, 17, 30, 50]:
        write_submission(test["CoilID"], ensemble_test, args.out_dir / f"submission_top{k}.csv", top_k=k)
    write_submission(test["CoilID"], ensemble_test, args.out_dir / "expected_submission.csv", top_k=17)
    ranked.to_csv(args.out_dir / "ranked_test_probabilities.csv", index=False)
    (args.out_dir / "validation_report.txt").write_text("\n".join(report), encoding="utf-8")


if __name__ == "__main__":
    main()
