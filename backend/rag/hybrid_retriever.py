from __future__ import annotations

import logging
import math
import os
import re
import threading
import time
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, List

from backend.config import ROOT_DIR, settings
from backend.telemetry.observability import metrics

logger = logging.getLogger(__name__)
MODEL_CACHE_DIR = Path(settings.model_cache_dir)
os.environ.setdefault("HF_HOME", str(MODEL_CACHE_DIR / "huggingface"))
os.environ.setdefault("SENTENCE_TRANSFORMERS_HOME", str(MODEL_CACHE_DIR / "sentence_transformers"))
os.environ.setdefault("TRANSFORMERS_CACHE", str(MODEL_CACHE_DIR / "transformers"))
os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
os.environ.setdefault("TRANSFORMERS_NO_ADVISORY_WARNINGS", "1")
os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")

TOKEN_PATTERN = re.compile(r"[a-zA-Z0-9_./-]+")


def tokenize(text: str) -> List[str]:
    return TOKEN_PATTERN.findall(str(text).lower())


class BM25Retriever:
    """Small dependency-free BM25 retriever for industrial maintenance documents."""

    def __init__(self, documents: List[Dict]) -> None:
        self.documents = documents
        self.doc_tokens = [tokenize(item.get("text", "")) for item in documents]
        self.doc_lengths = [len(tokens) for tokens in self.doc_tokens]
        self.avgdl = sum(self.doc_lengths) / max(1, len(self.doc_lengths))
        self.document_frequency: Counter[str] = Counter()
        for tokens in self.doc_tokens:
            self.document_frequency.update(set(tokens))

    def search(self, query: str, top_k: int = 12, filters: Dict | None = None) -> List[Dict]:
        filters = filters or {}
        query_terms = tokenize(query)
        scored = []
        for index, document in enumerate(self.documents):
            metadata = document.get("metadata", {})
            if any(metadata.get(key) != value for key, value in filters.items()):
                continue
            score = self._score(query_terms, self.doc_tokens[index], self.doc_lengths[index])
            if score > 0:
                scored.append({**document, "bm25_score": round(score, 4)})
        return sorted(scored, key=lambda item: item["bm25_score"], reverse=True)[:top_k]

    def _score(self, query_terms: Iterable[str], document_terms: List[str], doc_len: int) -> float:
        term_counts = Counter(document_terms)
        score = 0.0
        k1 = 1.5
        b = 0.75
        total_docs = max(1, len(self.documents))
        for term in query_terms:
            freq = term_counts.get(term, 0)
            if not freq:
                continue
            df = self.document_frequency.get(term, 0)
            idf = math.log(1 + (total_docs - df + 0.5) / (df + 0.5))
            denominator = freq + k1 * (1 - b + b * doc_len / max(1, self.avgdl))
            score += idf * (freq * (k1 + 1)) / max(denominator, 1e-9)
        return score


class Reranker:
    """Cross-encoder reranker with lexical fallback."""

    _model_instances: Dict[str, object] = {}
    _model_lock = threading.RLock()
    _resolved_model_paths: Dict[str, Dict] = {}
    _path_lock = threading.RLock()

    def __init__(self, model_name: str | None = None) -> None:
        self.model_name = model_name or settings.reranker_model
        self.model = None
        self.backend = "lexical_overlap" if settings.allow_model_fallback else "not_loaded"
        self.load_attempted = False
        self.last_load_breakdown: Dict[str, float | str | bool] = {}
        self.fallback_reason: str | None = None
        self.model_found = False
        self._lock = threading.RLock()
        self.rerank_cache: Dict[tuple, Dict] = {}
        self.rerank_cache_ttl_seconds = 15 * 60
        if settings.eager_load_ai_models:
            self._load_model()

    def _load_model(self) -> None:
        with self._lock:
            if self.load_attempted:
                return
            self.load_attempted = True
            if not settings.enable_runtime_model_loading and not settings.eager_load_ai_models:
                logger.info("Runtime reranker model loading disabled; using fast lexical reranker")
                return
            try:
                started = time.perf_counter()
                source = "memory_cache"
                phase_started = time.perf_counter()
                cache_diagnostic = model_cache_diagnostic(self.model_name)
                model_resolution_ms = round((time.perf_counter() - phase_started) * 1000, 2)
                breakdown: Dict[str, float | str | bool] = {
                    "cache_scan_ms": cache_diagnostic.get("cache_scan_ms", 0.0),
                    "model_resolution_ms": model_resolution_ms,
                    "model_download_ms": 0.0,
                    "model_deserialize_ms": 0.0,
                    "model_gpu_transfer_ms": 0.0,
                    "model_compile_ms": 0.0,
                    "module_import_ms": 0.0,
                    "numpy_compat_ms": 0.0,
                    "source": source,
                    "cache_dir": str(MODEL_CACHE_DIR),
                    "cache_directory": str(MODEL_CACHE_DIR),
                    "model_found": cache_diagnostic["model_found"],
                    "model_path": cache_diagnostic["model_path"],
                    "reranker_model_path": cache_diagnostic["model_path"],
                    "searched_paths": "; ".join(cache_diagnostic["searched_paths"]),
                    "cache_hit": bool(cache_diagnostic.get("cache_hit")),
                    "local_files_only": hf_local_files_only(),
                    "model_mode": settings.model_mode,
                    "fallback_reason": "",
                }
                self.model_found = bool(cache_diagnostic["model_found"])
                if settings.model_mode == "offline" and not self.model_found:
                    self.fallback_reason = (
                        f"model_not_found_in_local_cache model={self.model_name} "
                        f"cache_directory={MODEL_CACHE_DIR}"
                    )
                    breakdown["fallback_reason"] = self.fallback_reason
                    breakdown["total_ms"] = round((time.perf_counter() - started) * 1000, 2)
                    self.last_load_breakdown = breakdown
                    self.backend = "lexical_overlap" if settings.allow_model_fallback else "unavailable"
                    logger.warning(
                        "Reranker model missing in offline mode model=%s fallback_allowed=%s cache_directory=%s searched_paths=%s",
                        self.model_name,
                        settings.allow_model_fallback,
                        MODEL_CACHE_DIR,
                        cache_diagnostic["searched_paths"],
                    )
                    return
                with self._model_lock:
                    if self.model_name not in self._model_instances:
                        source = "local_cache_only" if hf_local_files_only() else "hub_allowed"
                        breakdown["source"] = source
                        phase_started = time.perf_counter()
                        from sentence_transformers import CrossEncoder
                        breakdown["module_import_ms"] = round((time.perf_counter() - phase_started) * 1000, 2)

                        phase_started = time.perf_counter()
                        model_reference = cache_diagnostic["model_path"] if cache_diagnostic["model_found"] and hf_local_files_only() else self.model_name
                        self._model_instances[self.model_name] = CrossEncoder(
                            model_reference,
                            local_files_only=hf_local_files_only(),
                        )
                        constructor_ms = round((time.perf_counter() - phase_started) * 1000, 2)
                        breakdown["model_load_ms"] = constructor_ms
                        breakdown["model_deserialize_ms"] = constructor_ms
                        breakdown["model_download_ms"] = constructor_ms if not hf_local_files_only() else 0.0
                    self.model = self._model_instances[self.model_name]
                self.model_found = True
                self.backend = "cross_encoder"
                total_ms = round((time.perf_counter() - started) * 1000, 2)
                breakdown["total_ms"] = total_ms
                self.last_load_breakdown = breakdown
                metrics.record("reranker_model_load", total_ms)
                metrics.record("reranker_model_download_ms", float(breakdown["model_download_ms"]))
                metrics.record("reranker_model_deserialize_ms", float(breakdown["model_deserialize_ms"]))
                metrics.record("reranker_model_gpu_transfer_ms", float(breakdown["model_gpu_transfer_ms"]))
                metrics.record("reranker_model_compile_ms", float(breakdown["model_compile_ms"]))
                logger.info(
                    "Reranker model ready model=%s source=%s local_files_only=%s timing=%s",
                    self.model_name,
                    source,
                    hf_local_files_only(),
                    breakdown,
                )
            except Exception as exc:
                self.fallback_reason = str(exc)
                self.last_load_breakdown = {
                    **(self.last_load_breakdown or {}),
                    "cache_directory": str(MODEL_CACHE_DIR),
                    "model_found": self.model_found,
                    "fallback_reason": self.fallback_reason,
                }
                self.backend = "lexical_overlap" if settings.allow_model_fallback else "unavailable"
                logger.warning("Reranker model unavailable fallback_allowed=%s error=%s", settings.allow_model_fallback, exc)

    def rerank(self, query: str, documents: List[Dict], top_k: int = 6, asset_id: str | None = None) -> List[Dict]:
        if not documents:
            return []
        cache_key = (query.strip().lower(), asset_id or "", tuple(item.get("id") for item in documents[:10]), top_k)
        cached = self.rerank_cache.get(cache_key)
        if cached and time.time() - float(cached.get("created_at", 0)) <= self.rerank_cache_ttl_seconds:
            return cached.get("results", [])
        if cached:
            self.rerank_cache.pop(cache_key, None)
        if self.model is None and not self.load_attempted:
            self._load_model()
        if self.model is not None:
            scores = self.model.predict([(query, item.get("text", "")) for item in documents])
            ranked = [
                {**document, "rerank_score": round(float(score), 4)}
                for document, score in zip(documents, scores)
            ]
        elif settings.allow_model_fallback:
            query_tokens = set(tokenize(query))
            ranked = []
            for document in documents:
                doc_tokens = set(tokenize(document.get("text", "")))
                overlap = len(query_tokens & doc_tokens) / max(1, len(query_tokens))
                hybrid_score = float(document.get("hybrid_score", document.get("score", 0)) or 0)
                ranked.append({**document, "rerank_score": round(overlap * 0.7 + hybrid_score * 0.3, 4)})
        else:
            raise RuntimeError(f"Reranker model unavailable and fallback disabled: {self.fallback_reason or self.model_name}")
        result = sorted(ranked, key=lambda item: item["rerank_score"], reverse=True)[:top_k]
        self.rerank_cache[cache_key] = {"created_at": time.time(), "results": result}
        return result

    def warmup(self) -> Dict:
        started = time.perf_counter()
        self._load_model()
        if self.model is None:
            latency_ms = round((time.perf_counter() - started) * 1000, 2)
            metrics.record("startup_reranker_ms", latency_ms)
            return {
                "model": self.model_name,
                "backend": self.backend,
                "latency_ms": latency_ms,
                "timing_breakdown": dict(self.last_load_breakdown),
                "real_model_loaded": False,
                "fallback_active": bool(settings.allow_model_fallback),
                "fallback_reason": self.fallback_reason or "model_unavailable",
                "model_found": self.model_found,
                "cache_directory": str(MODEL_CACHE_DIR),
            }
        phase_started = time.perf_counter()
        self.model.predict([("maintenance reliability warmup probe", "bearing inspection root cause evidence")])
        compile_ms = round((time.perf_counter() - phase_started) * 1000, 2)
        self.last_load_breakdown["model_compile_ms"] = round(float(self.last_load_breakdown.get("model_compile_ms", 0) or 0) + compile_ms, 2)
        metrics.record("reranker_model_compile_ms", compile_ms)
        latency_ms = round((time.perf_counter() - started) * 1000, 2)
        metrics.record("startup_reranker_ms", latency_ms)
        return {
            "model": self.model_name,
            "backend": self.backend,
            "latency_ms": latency_ms,
            "timing_breakdown": dict(self.last_load_breakdown),
            "real_model_loaded": self.model is not None,
            "fallback_active": False,
            "fallback_reason": self.fallback_reason,
            "model_found": self.model_found,
            "cache_directory": str(MODEL_CACHE_DIR),
        }

    def health_status(self) -> Dict:
        return {
            "status": "healthy",
            "model": self.model_name,
            "backend": self.backend,
            "real_model_loaded": self.model is not None,
            "timing_breakdown": dict(self.last_load_breakdown),
            "fallback_active": bool(self.model is None and settings.allow_model_fallback),
            "fallback_reason": self.fallback_reason,
            "model_found": self.model_found,
            "cache_directory": str(MODEL_CACHE_DIR),
            "lazy_loading": not settings.eager_load_ai_models,
            "load_attempted": self.load_attempted,
            "cache_size": len(self.rerank_cache),
        }


def hf_local_files_only() -> bool:
    if settings.model_mode == "download_if_missing":
        return False
    return os.getenv("HF_LOCAL_FILES_ONLY", os.getenv("TRANSFORMERS_OFFLINE", "true")).lower() == "true"


def hf_cache_dir_name(model_id: str) -> str:
    return "models--" + str(model_id).replace("/", "--")


def candidate_model_ids(model_name: str) -> List[str]:
    names = [str(model_name)]
    if "/" not in str(model_name):
        names.append(f"cross-encoder/{model_name}")
    return list(dict.fromkeys(names))


def model_cache_diagnostic(model_name: str) -> Dict:
    cache_key = f"{MODEL_CACHE_DIR.resolve()}::{model_name}::{hf_local_files_only()}"
    with Reranker._path_lock:
        cached = Reranker._resolved_model_paths.get(cache_key)
        if cached:
            return {
                **cached,
                "cache_hit": True,
                "cache_scan_ms": 0.0,
            }
    started = time.perf_counter()
    logger.info("Reranker cache scan start model=%s cache_directory=%s", model_name, MODEL_CACHE_DIR)
    searched = []
    for model_id in candidate_model_ids(model_name):
        for base in model_cache_bases():
            candidates = [
                base / model_id,
                base / model_id.replace("/", "_"),
                base / hf_cache_dir_name(model_id),
            ]
            for path in candidates:
                searched.append(str(path))
                snapshot = resolve_model_snapshot(path)
                if snapshot:
                    result = {
                        "cache_directory": str(MODEL_CACHE_DIR),
                        "model_found": True,
                        "model_path": str(snapshot),
                        "searched_paths": searched,
                        "cache_hit": False,
                        "cache_scan_ms": round((time.perf_counter() - started) * 1000, 2),
                    }
                    with Reranker._path_lock:
                        Reranker._resolved_model_paths[cache_key] = dict(result)
                    logger.info(
                        "Reranker cache scan finish model=%s found=True path=%s cache_scan_ms=%s searched=%s",
                        model_name,
                        snapshot,
                        result["cache_scan_ms"],
                        len(searched),
                    )
                    return result
    result = {
        "cache_directory": str(MODEL_CACHE_DIR),
        "model_found": False,
        "model_path": "",
        "searched_paths": searched,
        "cache_hit": False,
        "cache_scan_ms": round((time.perf_counter() - started) * 1000, 2),
    }
    with Reranker._path_lock:
        Reranker._resolved_model_paths[cache_key] = dict(result)
    logger.info(
        "Reranker cache scan finish model=%s found=False cache_scan_ms=%s searched=%s",
        model_name,
        result["cache_scan_ms"],
        len(searched),
    )
    return result


def model_cache_bases() -> List[Path]:
    bases = [
        MODEL_CACHE_DIR / "sentence_transformers",
        MODEL_CACHE_DIR / "huggingface" / "hub",
        MODEL_CACHE_DIR / "transformers",
        Path(os.environ.get("HF_HOME", "")) / "hub" if os.environ.get("HF_HOME") else Path(),
        Path.home() / ".cache" / "huggingface" / "hub",
        Path.home() / ".cache" / "sentence_transformers",
    ]
    unique = []
    for base in bases:
        if not str(base) or str(base) == ".":
            continue
        if str(base) not in [str(item) for item in unique]:
            unique.append(base)
    return unique


def resolve_model_snapshot(path: Path) -> Path | None:
    if not path.exists():
        return None
    if _looks_like_model_dir(path):
        return path
    snapshots_dir = path / "snapshots"
    if snapshots_dir.is_dir():
        try:
            snapshots = sorted(
                (item for item in snapshots_dir.iterdir() if item.is_dir()),
                key=lambda item: item.stat().st_mtime,
                reverse=True,
            )
        except OSError:
            snapshots = []
        for snapshot in snapshots:
            if _looks_like_model_dir(snapshot):
                return snapshot
    try:
        for child in path.iterdir():
            if child.is_dir() and _looks_like_model_dir(child):
                return child
    except OSError:
        return None
    return None


def _looks_like_model_dir(path: Path) -> bool:
    if (path / "modules.json").exists():
        return True
    if not (path / "config.json").exists():
        return False
    return any(path.glob("*.safetensors")) or any(path.glob("pytorch_model*")) or any(path.glob("*.bin"))
