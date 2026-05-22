from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel


class AIOVGenerateRequest(BaseModel):
    included_evidence_item_ids: list[uuid.UUID] | None = None
    included_research_source_ids: list[uuid.UUID] | None = None
    notes: str = ""


class AIOVAnalysisOut(BaseModel):
    id: uuid.UUID
    version: int
    status: str
    analysis_json: dict
    narrative: str | None
    missing_evidence_json: dict | None
    created_at: datetime

    model_config = {"from_attributes": True}
