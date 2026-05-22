from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, uuid_pk


class SourceLane(str, enum.Enum):
    PRIVATE_EVIDENCE = "PRIVATE_EVIDENCE"
    PUBLIC_WEB = "PUBLIC_WEB"
    INTERNAL_COMPARABLES = "INTERNAL_COMPARABLES"
    MIXED = "MIXED"


class ResearchStatus(str, enum.Enum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class EvidenceClassification(str, enum.Enum):
    MANUFACTURER_SPEC = "MANUFACTURER_SPEC"
    LISTING_PRICE = "LISTING_PRICE"
    CONFIRMED_SALE_PRICE = "CONFIRMED_SALE_PRICE"
    AUCTION_RESULT = "AUCTION_RESULT"
    BENCHMARK_REFERENCE = "BENCHMARK_REFERENCE"
    MARKET_COMMENTARY = "MARKET_COMMENTARY"
    UNKNOWN = "UNKNOWN"


class ResearchSession(Base, TimestampMixin):
    __tablename__ = "research_sessions"

    id: Mapped = uuid_pk()
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    asset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("assets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    initiated_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    query: Mapped[str] = mapped_column(Text, nullable=False)
    source_lane: Mapped[SourceLane] = mapped_column(
        Enum(SourceLane, name="source_lane_enum"), nullable=False
    )
    provider: Mapped[str | None] = mapped_column(String(64))
    model_used: Mapped[str | None] = mapped_column(String(128))
    status: Mapped[ResearchStatus] = mapped_column(
        Enum(ResearchStatus, name="research_status_enum"),
        default=ResearchStatus.PENDING,
        nullable=False,
    )

    sources = relationship(
        "ResearchSource", back_populates="session", cascade="all, delete-orphan"
    )


class ResearchSource(Base, TimestampMixin):
    __tablename__ = "research_sources"

    id: Mapped = uuid_pk()
    research_session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("research_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_type: Mapped[str] = mapped_column(String(32), nullable=False)
    title: Mapped[str | None] = mapped_column(String(512))
    source_url: Mapped[str | None] = mapped_column(String(2048))
    publisher_domain: Mapped[str | None] = mapped_column(String(255))
    retrieved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    evidence_classification: Mapped[EvidenceClassification] = mapped_column(
        Enum(EvidenceClassification, name="evidence_classification_enum"),
        default=EvidenceClassification.UNKNOWN,
        nullable=False,
    )
    content_excerpt: Mapped[str | None] = mapped_column(Text)
    source_hash: Mapped[str | None] = mapped_column(String(64))
    validator_status: Mapped[str | None] = mapped_column(String(32))
    extra_metadata: Mapped[dict | None] = mapped_column(JSONB)

    session = relationship("ResearchSession", back_populates="sources")
