from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

from backend.config import DATA_DIR


def load_documents(data_dir: Path = DATA_DIR) -> List[Dict]:
    documents: List[Dict] = []
    text_sources = [
        ("manual", data_dir / "equipment_manuals.md"),
        ("sop", data_dir / "maintenance_sops.md"),
        ("failure_analysis", data_dir / "failure_analysis_reports.md"),
    ]
    for source, path in text_sources:
        if path.exists():
            documents.append({"id": path.stem, "text": path.read_text(encoding="utf-8"), "metadata": {"source": source}})
    json_sources = [
        ("failure_reports", "failure_reports.json"),
        ("maintenance_logs", "maintenance_logs.json"),
        ("work_orders", "work_orders.json"),
        ("spare_parts", "spare_parts.json"),
    ]
    for source, filename in json_sources:
        path = data_dir / filename
        if not path.exists():
            continue
        for index, row in enumerate(json.loads(path.read_text(encoding="utf-8"))):
            documents.append(
                {
                    "id": f"{source}-{index}",
                    "text": json.dumps(row, ensure_ascii=False),
                    "metadata": {"source": source, "equipment_id": row.get("equipment_id")},
                }
            )
    return documents


def chunk_documents(documents: List[Dict], chunk_size: int = 900, overlap: int = 120) -> List[Dict]:
    chunks: List[Dict] = []
    for document in documents:
        text = document["text"]
        start = 0
        chunk_index = 0
        while start < len(text):
            end = min(len(text), start + chunk_size)
            chunks.append(
                {
                    "id": f"{document['id']}-{chunk_index}",
                    "text": text[start:end],
                    "metadata": {**document.get("metadata", {}), "parent_id": document["id"]},
                }
            )
            chunk_index += 1
            start = max(end - overlap, end)
    return chunks
