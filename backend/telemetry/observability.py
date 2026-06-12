from __future__ import annotations

import json
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Dict, Iterator

from backend.config import OUTPUT_DIR


class MetricsRegistry:
    def __init__(self) -> None:
        self.metrics: Dict[str, list[float]] = {}
        self.last_request_metrics: Dict[str, float | str | bool | None] = {}

    @contextmanager
    def span(self, name: str) -> Iterator[None]:
        started = time.perf_counter()
        try:
            yield
        finally:
            self.record(name, (time.perf_counter() - started) * 1000)

    def record(self, name: str, latency_ms: float) -> None:
        self.metrics.setdefault(name, []).append(round(latency_ms, 2))
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        with (OUTPUT_DIR / "observability.jsonl").open("a", encoding="utf-8") as handle:
            handle.write(json.dumps({"stage": name, "latency_ms": round(latency_ms, 2), "ts": time.time()}) + "\n")

    def record_request(self, **values) -> None:
        payload = {"ts": time.time(), **values}
        normalized = {}
        for key, value in payload.items():
            if isinstance(value, bool):
                normalized[key] = value
            elif isinstance(value, (int, float)):
                normalized[key] = round(float(value), 2)
            else:
                normalized[key] = value
        self.last_request_metrics = normalized
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        with (OUTPUT_DIR / "observability.jsonl").open("a", encoding="utf-8") as handle:
            handle.write(json.dumps({"stage": "last_request_metrics", **normalized}) + "\n")

    def summary(self) -> Dict[str, Dict[str, float]]:
        return {
            name: {
                "count": len(values),
                "avg_ms": round(sum(values) / max(1, len(values)), 2),
                "max_ms": round(max(values), 2),
            }
            for name, values in self.metrics.items()
        }

    def latest_request(self) -> Dict[str, float | str | bool | None]:
        return dict(self.last_request_metrics)


metrics = MetricsRegistry()
