from __future__ import annotations

import argparse
import os
import time
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent
DEFAULT_CACHE_DIR = ROOT_DIR / ".model_cache"
DEFAULT_EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
DEFAULT_RERANKER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"


def configure_cache(cache_dir: Path) -> None:
    cache_dir.mkdir(parents=True, exist_ok=True)
    os.environ["MODEL_MODE"] = "download_if_missing"
    os.environ["MODEL_CACHE_DIR"] = str(cache_dir)
    os.environ["HF_HOME"] = str(cache_dir / "huggingface")
    os.environ["SENTENCE_TRANSFORMERS_HOME"] = str(cache_dir / "sentence_transformers")
    os.environ["TRANSFORMERS_CACHE"] = str(cache_dir / "transformers")
    os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
    os.environ.setdefault("TRANSFORMERS_NO_ADVISORY_WARNINGS", "1")
    os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")


def download_embedding(model_name: str) -> None:
    from sentence_transformers import SentenceTransformer

    started = time.perf_counter()
    model = SentenceTransformer(model_name, cache_folder=os.environ["SENTENCE_TRANSFORMERS_HOME"])
    vector = model.encode(["Maintenance Wizard model cache validation"], normalize_embeddings=True)
    print(
        {
            "model": model_name,
            "kind": "embedding",
            "dimension": len(vector[0]),
            "download_ms": round((time.perf_counter() - started) * 1000, 2),
        }
    )


def download_reranker(model_name: str) -> None:
    from sentence_transformers import CrossEncoder

    started = time.perf_counter()
    model = CrossEncoder(model_name)
    score = model.predict([("hydraulic pressure low", "hydraulic actuator seal leakage")])[0]
    print(
        {
            "model": model_name,
            "kind": "reranker",
            "score": float(score),
            "download_ms": round((time.perf_counter() - started) * 1000, 2),
        }
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Download Maintenance Wizard AI models into the local project cache.")
    parser.add_argument("--cache-dir", default=str(DEFAULT_CACHE_DIR), help="Target model cache directory.")
    parser.add_argument("--embedding-model", default=DEFAULT_EMBEDDING_MODEL)
    parser.add_argument("--reranker-model", default=DEFAULT_RERANKER_MODEL)
    args = parser.parse_args()

    cache_dir = Path(args.cache_dir).resolve()
    configure_cache(cache_dir)
    print({"cache_directory": str(cache_dir), "mode": "download_if_missing"})
    download_embedding(args.embedding_model)
    download_reranker(args.reranker_model)
    print("Model download complete. Restart the FastAPI server with MODEL_MODE=offline to use cached models.")


if __name__ == "__main__":
    main()
