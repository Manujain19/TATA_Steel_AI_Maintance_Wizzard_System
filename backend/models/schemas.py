from __future__ import annotations

from typing import Any, Dict, List, Optional

try:
    from pydantic import BaseModel, Field
except Exception:  # pragma: no cover - lets source compile without optional deps
    class BaseModel:  # type: ignore
        pass

    def Field(default=None, **_: Any):  # type: ignore
        return default


class AssetQuery(BaseModel):
    equipment_id: Optional[str] = None
    query: str = ""


class CopilotRequest(BaseModel):
    equipment_id: Optional[str] = None
    message: str
    history: List[Dict[str, Any]] = Field(default_factory=list)


class SearchRequest(BaseModel):
    query: str
    equipment_id: Optional[str] = None
    filters: Dict[str, Any] = Field(default_factory=dict)


class ReportRequest(BaseModel):
    report_type: str = "executive_summary"
    export_format: str = "json"
    equipment_id: Optional[str] = None
