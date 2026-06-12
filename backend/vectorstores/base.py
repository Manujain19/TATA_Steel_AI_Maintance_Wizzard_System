from __future__ import annotations

import math
from typing import Dict, List, Protocol


class VectorStore(Protocol):
    def add_documents(self, documents: List[Dict], embeddings: List[List[float]]) -> None: ...
    def search(self, embedding: List[float], top_k: int = 6, filters: Dict | None = None) -> List[Dict]: ...


def cosine(left: List[float], right: List[float]) -> float:
    total = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(a * a for a in left)) or 1.0
    right_norm = math.sqrt(sum(b * b for b in right)) or 1.0
    return total / (left_norm * right_norm)


class InMemoryVectorStore:
    def __init__(self) -> None:
        self.rows: List[Dict] = []
        self.collection_name = "in_memory_maintenance_knowledge"

    def add_documents(self, documents: List[Dict], embeddings: List[List[float]]) -> None:
        for document, embedding in zip(documents, embeddings):
            self.rows.append({"document": document, "embedding": embedding})

    def search(self, embedding: List[float], top_k: int = 6, filters: Dict | None = None) -> List[Dict]:
        filters = filters or {}
        scored = []
        for row in self.rows:
            metadata = row["document"].get("metadata", {})
            if any(metadata.get(key) != value for key, value in filters.items()):
                continue
            scored.append({**row["document"], "score": round(cosine(embedding, row["embedding"]), 4)})
        return sorted(scored, key=lambda item: item["score"], reverse=True)[:top_k]

    def status(self) -> Dict:
        return {
            "backend": "in_memory",
            "collection": self.collection_name,
            "available": True,
            "document_count": len(self.rows),
            "fallback": True,
        }
