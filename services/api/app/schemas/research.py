from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class PrivateResearchRequest(BaseModel):
    query: str


class PublicResearchRequest(BaseModel):
    query: str
    maximum_number_of_urls: int = Field(default=10, ge=1, le=25)
    maximum_number_of_tokens: int = Field(default=8192, ge=512, le=32768)
    context_threshold_mode: str = "balanced"


class EbayResearchRequest(BaseModel):
    query: str
    limit: int = Field(default=10, ge=1, le=50)
    include_sold_comps: bool = Field(
        default=True,
        description="Also call Marketplace Insights for sold comps · requires business approval.",
    )
    marketplace_id: str | None = None


class ResearchSourceOut(BaseModel):
    id: uuid.UUID
    source_type: str
    title: str | None
    source_url: str | None
    publisher_domain: str | None
    retrieved_at: datetime | None
    evidence_classification: str
    content_excerpt: str | None
    source_hash: str | None
    validator_status: str | None

    model_config = {"from_attributes": True}


class ResearchSessionOut(BaseModel):
    id: uuid.UUID
    query: str
    source_lane: str
    provider: str | None
    model_used: str | None
    status: str
    created_at: datetime
    sources: list[ResearchSourceOut] = []
