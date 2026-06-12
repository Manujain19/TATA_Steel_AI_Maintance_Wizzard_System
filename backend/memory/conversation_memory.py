from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from backend.config import OUTPUT_DIR


class ConversationMemory:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or OUTPUT_DIR / "backend_conversation_memory.jsonl"

    def append(self, equipment_id: str, payload: Dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps({"equipment_id": equipment_id, **payload}) + "\n")

    def load(self, equipment_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        if not self.path.exists():
            return []
        rows = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("equipment_id") == equipment_id:
                rows.append(row)
        return rows[-limit:]
