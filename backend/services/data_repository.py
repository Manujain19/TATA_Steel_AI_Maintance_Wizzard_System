from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from backend.config import DATA_DIR


class DataRepository:
    """Repository facade over JSON seed data, with Postgres-ready boundaries."""

    def __init__(self, data_dir: Path = DATA_DIR) -> None:
        self.data_dir = data_dir
        self._cache: Dict[str, Any] = {}

    def _read_json(self, name: str, fallback: Any) -> Any:
        if name in self._cache:
            return self._cache[name]
        path = self.data_dir / name
        if not path.exists():
            return fallback
        value = json.loads(path.read_text(encoding="utf-8"))
        self._cache[name] = value
        return value

    def assets(self) -> List[Dict[str, Any]]:
        return self._read_json("equipment.json", [])

    def sensors(self) -> List[Dict[str, Any]]:
        return self._read_json("sensor_data.json", [])

    def sensor_history(self) -> List[Dict[str, Any]]:
        return self._read_json("sensor_data_full.json", [])

    def failure_modes(self) -> List[Dict[str, Any]]:
        return self._read_json("failure_modes.json", [])

    def failure_reports(self) -> List[Dict[str, Any]]:
        return self._read_json("failure_reports.json", [])

    def maintenance_logs(self) -> List[Dict[str, Any]]:
        return self._read_json("maintenance_logs.json", [])

    def spare_parts(self) -> List[Dict[str, Any]]:
        return self._read_json("spare_parts.json", [])

    def work_orders(self) -> List[Dict[str, Any]]:
        return self._read_json("work_orders.json", [])

    def asset_bundle(self, equipment_id: str) -> Dict[str, Any]:
        return {
            "asset": next((item for item in self.assets() if item.get("id") == equipment_id), None),
            "sensor": next((item for item in self.sensors() if item.get("equipment_id") == equipment_id), None),
            "sensor_history": [item for item in self.sensor_history() if item.get("equipment_id") == equipment_id],
            "failure_modes": [item for item in self.failure_modes() if item.get("equipment_id") == equipment_id],
            "failure_reports": [item for item in self.failure_reports() if item.get("equipment_id") == equipment_id],
            "maintenance_logs": [item for item in self.maintenance_logs() if item.get("equipment_id") == equipment_id],
            "spare_parts": [item for item in self.spare_parts() if item.get("equipment_id") == equipment_id],
            "work_orders": [item for item in self.work_orders() if item.get("equipment_id") == equipment_id],
        }
