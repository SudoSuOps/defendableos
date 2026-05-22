from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel


class AuditEventOut(BaseModel):
    id: uuid.UUID
    actor_type: str
    actor_id: str | None
    action: str
    entity_type: str
    entity_id: str
    extra_metadata: dict | None
    created_at: datetime

    model_config = {"from_attributes": True}
