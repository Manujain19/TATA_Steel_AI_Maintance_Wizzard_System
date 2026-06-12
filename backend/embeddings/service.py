from __future__ import annotations

import hashlib
import logging
import math
import os
import threading
import time
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


SUPPORTED_EMBEDDING_MODELS = {
    "BAAI/bge-large-en-v1.5",
    "all-MiniLM-L6-v2",
    "nomic-embed-text",
}

MODEL_DIMENSIONS = {
    "all-MiniLM-L6-v2": 384,
    "sentence-transformers/all-MiniLM-L6-v2": 384,
    "BAAI/bge-large-en-v1.5": 1024,
    "nomic-embed-text": 768,
}


class EmbeddingService:
    """Production embedding facade with SentenceTransformers and deterministic fallback."""

    _model_instances: Dict[str, object] = {}
    _model_dimensions: Dict[str, int] = {}
    _model_lock = threading.RLock()
    _resolved_model_paths: Dict[str, Dict] = {}
    _path_lock = threading.RLock()

    def __init__(self, model_name: str | None = None) -> None:
        self.model_name = model_name or settings.embedding_model
        self.model = None
        self.backend = "deterministic_hash" if settings.allow_model_fallback else "not_loaded"
        self.dimensions = expected_dimensions(self.model_name)
        self.load_attempted = False
        self.last_load_breakdown: Dict[str, float | str | bool] = {}
        self.fallback_reason: str | None = None
        self.model_found = False
        self.embedding_cache: Dict[str, List[float]] = {}
        self.cache_hits = 0
        self._lock = threading.RLock()
        if settings.eager_load_ai_models:
            self._load_model()

    def _load_model(self) -> None:
        with self._lock:
            if self.load_attempted:
                return
            self.load_attempted = True
            if not settings.enable_runtime_model_loading and not settings.eager_load_ai_models:
                logger.info("Runtime embedding model loading disabled; using deterministic embedding cache mode")
                return
            if self.model_name == "nomic-embed-text":
                logger.info("Embedding model nomic-embed-text configured; using local deterministic fallback unless Ollama adapter is enabled")
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
                    "embedding_model_path": cache_diagnostic["model_path"],
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
                    self.backend = "deterministic_hash" if settings.allow_model_fallback else "unavailable"
                    logger.warning(
                        "Embedding model missing in offline mode model=%s fallback_allowed=%s cache_directory=%s searched_paths=%s",
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
                        from sentence_transformers import SentenceTransformer
                        breakdown["module_import_ms"] = round((time.perf_counter() - phase_started) * 1000, 2)

                        phase_started = time.perf_counter()
                        model_reference = cache_diagnostic["model_path"] if cache_diagnostic["model_found"] and hf_local_files_only() else self.model_name
                        self._model_instances[self.model_name] = SentenceTransformer(
                            model_reference,
                            local_files_only=hf_local_files_only(),
                        )
                        constructor_ms = round((time.perf_counter() - phase_started) * 1000, 2)
                        breakdown["model_load_ms"] = constructor_ms
                        breakdown["model_deserialize_ms"] = constructor_ms
                        breakdown["model_download_ms"] = constructor_ms if not hf_local_files_only() else 0.0
                    self.model = self._model_instances[self.model_name]
                self.model_found = True
                self.backend = "sentence_transformers"
                if self.model_name not in self._model_dimensions:
                    phase_started = time.perf_counter()
                    probe = self.model.encode(["health probe"], normalize_embeddings=True)
                    breakdown["model_compile_ms"] = round((time.perf_counter() - phase_started) * 1000, 2)
                    self._model_dimensions[self.model_name] = len(probe[0])
                self.dimensions = self._model_dimensions[self.model_name]
                total_ms = round((time.perf_counter() - started) * 1000, 2)
                breakdown["total_ms"] = total_ms
                self.last_load_breakdown = breakdown
                metrics.record("embedding_model_load", total_ms)
                metrics.record("embedding_model_download_ms", float(breakdown["model_download_ms"]))
                metrics.record("embedding_model_deserialize_ms", float(breakdown["model_deserialize_ms"]))
                metrics.record("embedding_model_gpu_transfer_ms", float(breakdown["model_gpu_transfer_ms"]))
                metrics.record("embedding_model_compile_ms", float(breakdown["model_compile_ms"]))
                logger.info(
                    "Embedding model ready model=%s dimensions=%s source=%s local_files_only=%s timing=%s",
                    self.model_name,
                    self.dimensions,
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
                self.backend = "deterministic_hash" if settings.allow_model_fallback else "unavailable"
                logger.warning("Embedding model unavailable fallback_allowed=%s error=%s", settings.allow_model_fallback, exc)
                self.model = None
                self.dimensions = expected_dimensions(self.model_name)

    def generate_embedding(self, text: str) -> List[float]:
        return self.batch_generate_embeddings([text])[0]

    def batch_generate_embeddings(self, documents: Iterable[str]) -> List[List[float]]:
        texts = [str(item) for item in documents]
        if self.model is None and not self.load_attempted:
            self._load_model()
        with self._lock:
            missing = [text for text in texts if text not in self.embedding_cache]
            self.cache_hits += len(texts) - len(missing)
            if missing:
                if self.model is not None:
                    vectors = self.model.encode(missing, normalize_embeddings=True)
                    for text, vector in zip(missing, vectors):
                        self.embedding_cache[text] = [round(float(value), 6) for value in vector]
                elif settings.allow_model_fallback:
                    for text in missing:
                        self.embedding_cache[text] = self._hash_embedding(text)
                else:
                    raise RuntimeError(f"Embedding model unavailable and fallback disabled: {self.fallback_reason or self.model_name}")
            return [self.embedding_cache[text] for text in texts]

    def generate_embeddings(self, texts: Iterable[str]) -> List[List[float]]:
        return self.batch_generate_embeddings(texts)

    def warmup(self) -> Dict:
        started = time.perf_counter()
        self._load_model()
        if self.model is None:
            latency_ms = round((time.perf_counter() - started) * 1000, 2)
            metrics.record("startup_embedding_ms", latency_ms)
            return {
                "model": self.model_name,
                "backend": self.backend,
                "dimensions": self.dimensions,
                "latency_ms": latency_ms,
                "timing_breakdown": dict(self.last_load_breakdown),
                "real_model_loaded": False,
                "fallback_active": bool(settings.allow_model_fallback),
                "fallback_reason": self.fallback_reason or "model_unavailable",
                "model_found": self.model_found,
                "cache_directory": str(MODEL_CACHE_DIR),
            }
        self.batch_generate_embeddings(["maintenance reliability warmup probe"])
        latency_ms = round((time.perf_counter() - started) * 1000, 2)
        metrics.record("startup_embedding_ms", latency_ms)
        return {
            "model": self.model_name,
            "backend": self.backend,
            "dimensions": self.dimensions,
            "latency_ms": latency_ms,
            "timing_breakdown": dict(self.last_load_breakdown),
            "real_model_loaded": self.model is not None,
            "fallback_active": False,
            "fallback_reason": self.fallback_reason,
            "model_found": self.model_found,
            "cache_directory": str(MODEL_CACHE_DIR),
        }

    def _hash_embedding(self, text: str, dimensions: int | None = None) -> List[float]:
        dimensions = int(dimensions or self.dimensions or expected_dimensions(self.model_name))
        buckets = [0.0] * dimensions
        for token in text.lower().split():
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:2], "big") % dimensions
            buckets[index] += 1.0
        norm = math.sqrt(sum(value * value for value in buckets)) or 1.0
        return [round(value / norm, 6) for value in buckets]

    def index_documents(self, vector_store, documents: List[Dict]) -> None:
        texts = [doc["text"] for doc in documents]
        embeddings = self.batch_generate_embeddings(texts)
        vector_store.add_documents(documents, embeddings)

    def semantic_search(self, vector_store, query: str, top_k: int = 6, filters: Dict | None = None) -> List[Dict]:
        embedding = self.generate_embedding(query)
        return vector_store.search(embedding, top_k=top_k, filters=filters or {})

    def health_status(self) -> Dict:
        return {
            "status": "healthy",
            "model": self.model_name,
            "supported_models": sorted(SUPPORTED_EMBEDDING_MODELS),
            "backend": self.backend,
            "dimensions": self.dimensions,
            "real_model_loaded": self.model is not None,
            "timing_breakdown": dict(self.last_load_breakdown),
            "fallback_active": bool(self.model is None and settings.allow_model_fallback),
            "fallback_reason": self.fallback_reason,
            "model_found": self.model_found,
            "cache_directory": str(MODEL_CACHE_DIR),
            "lazy_loading": not settings.eager_load_ai_models,
            "load_attempted": self.load_attempted,
            "cache_size": len(self.embedding_cache),
            "cache_hits": self.cache_hits,
        }


def expected_dimensions(model_name: str) -> int:
    return MODEL_DIMENSIONS.get(str(model_name or ""), 384)


def hf_local_files_only() -> bool:
    if settings.model_mode == "download_if_missing":
        return False
    return os.getenv("HF_LOCAL_FILES_ONLY", os.getenv("TRANSFORMERS_OFFLINE", "true")).lower() == "true"


def candidate_model_ids(model_name: str) -> List[str]:
    names = [str(model_name)]
    if "/" not in str(model_name):
        names.append(f"sentence-transformers/{model_name}")
    return list(dict.fromkeys(names))


def hf_cache_dir_name(model_id: str) -> str:
    return "models--" + str(model_id).replace("/", "--")


def model_cache_diagnostic(model_name: str) -> Dict:
    cache_key = f"{MODEL_CACHE_DIR.resolve()}::{model_name}::{hf_local_files_only()}"
    with EmbeddingService._path_lock:
        cached = EmbeddingService._resolved_model_paths.get(cache_key)
        if cached:
            return {
                **cached,
                "cache_hit": True,
                "cache_scan_ms": 0.0,
            }
    started = time.perf_counter()
    logger.info("Embedding cache scan start model=%s cache_directory=%s", model_name, MODEL_CACHE_DIR)
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
                    with EmbeddingService._path_lock:
                        EmbeddingService._resolved_model_paths[cache_key] = dict(result)
                    logger.info(
                        "Embedding cache scan finish model=%s found=True path=%s cache_scan_ms=%s searched=%s",
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
    with EmbeddingService._path_lock:
        EmbeddingService._resolved_model_paths[cache_key] = dict(result)
    logger.info(
        "Embedding cache scan finish model=%s found=False cache_scan_ms=%s searched=%s",
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
