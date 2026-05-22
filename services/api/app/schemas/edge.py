from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel


class EdgeEnrollmentTokenCreate(BaseModel):
    node_name_hint: str | None = None
    ttl_minutes: int | None = None


class EdgeEnrollmentTokenOut(BaseModel):
    id: uuid.UUID
    token: str  # plaintext shown ONCE at creation
    node_name_hint: str | None
    expires_at: datetime

    model_config = {"from_attributes": True}


class EdgeEnrollRequest(BaseModel):
    token: str
    node_name: str
    software_version: str | None = None
    hardware_summary: dict | None = None
    public_key_or_device_fingerprint: str | None = None


class EdgeEnrollResponse(BaseModel):
    node_id: uuid.UUID
    edge_token: str
    ens_name: str | None


class EdgeHeartbeatRequest(BaseModel):
    software_version: str | None = None
    hardware_summary: dict | None = None


class EdgeNodeOut(BaseModel):
    id: uuid.UUID
    node_name: str
    node_slug: str
    enrollment_status: str
    last_heartbeat_at: datetime | None
    software_version: str | None
    ens_identity_id: uuid.UUID | None
    created_at: datetime

    model_config = {"from_attributes": True}
