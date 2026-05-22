from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel


class ValidatorReviewOut(BaseModel):
    id: uuid.UUID
    version: int
    status: str
    protocol: str
    receipt_sha256: str
    checks_json: list[dict]
    findings_json: list[dict] | None
    created_at: datetime

    model_config = {"from_attributes": True}
