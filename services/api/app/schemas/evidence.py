from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel


class EvidenceItemOut(BaseModel):
    id: uuid.UUID
    filename: str
    evidence_type: str
    visibility: str
    ingestion_status: str
    sha256_hash: str | None
    content_type: str | None
    byte_size: int
    provenance: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class EvidenceManifestOut(BaseModel):
    id: uuid.UUID
    version: int
    manifest_sha256: str
    status: str
    item_count: int
    created_at: datetime
