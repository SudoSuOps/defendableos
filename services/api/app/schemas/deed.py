from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel


class DeedOut(BaseModel):
    id: uuid.UUID
    deed_reference: str
    version: int
    status: str
    is_public: bool
    public_slug: str | None
    record_hash: str
    deed_json: dict
    created_at: datetime

    model_config = {"from_attributes": True}


class PublishDeedRequest(BaseModel):
    # Reserved for future fields · admin-only action gating handled by RBAC.
    pass
