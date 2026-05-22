from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel


class ENSReservationRequest(BaseModel):
    label: str
    identity_type: str  # ORGANIZATION | ASSET | DEED | EDGE_NODE
    organization_id: uuid.UUID
    asset_id: uuid.UUID | None = None
    deed_id: uuid.UUID | None = None
    edge_node_id: uuid.UUID | None = None
    public_metadata: dict | None = None


class ENSIdentityOut(BaseModel):
    id: uuid.UUID
    ens_name: str
    label: str
    parent_name: str
    identity_type: str
    issuance_mode: str
    status: str
    public_metadata_json: dict | None
    transaction_hash: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
