from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field


class ComputeProfileIn(BaseModel):
    manufacturer: str | None = None
    model: str | None = None
    gpu_count: int | None = None
    vram_per_gpu_gb: int | None = None
    cpu: str | None = None
    ram_gb: int | None = None
    storage_description: str | None = None
    networking_description: str | None = None
    operating_system: str | None = None
    condition_status: str | None = None
    operational_status: str | None = None
    intended_use: str | None = None
    purchase_date: date | None = None
    purchase_cost_private: float | None = None


class AssetCreateRequest(BaseModel):
    name: str
    asset_class: str = "COMPUTE_HARDWARE"
    category: str | None = None
    description: str | None = None
    private_serial_number: str | None = None
    client_internal_reference: str | None = None
    public_asset_reference: str | None = Field(
        default=None, description="If omitted, the API auto-generates a deterministic reference."
    )
    compute_profile: ComputeProfileIn | None = None


class AssetSummary(BaseModel):
    id: uuid.UUID
    public_asset_reference: str
    name: str
    asset_class: str
    category: str | None
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class AssetOut(AssetSummary):
    organization_id: uuid.UUID
    description: str | None
    compute_profile: ComputeProfileIn | None = None
