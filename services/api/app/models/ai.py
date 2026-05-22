from __future__ import annotations

import enum
import uuid

from sqlalchemy import Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, uuid_pk


class WorkflowType(str, enum.Enum):
    EVIDENCE_SUMMARY = "EVIDENCE_SUMMARY"
    RESEARCH_SYNTHESIS = "RESEARCH_SYNTHESIS"
    AIOV_DRAFT = "AIOV_DRAFT"
    VALIDATOR_ASSIST = "VALIDATOR_ASSIST"
    PUBLIC_DEED_SUMMARY = "PUBLIC_DEED_SUMMARY"
    EDGE_EVIDENCE_CLASSIFICATION = "EDGE_EVIDENCE_CLASSIFICATION"


class AIOutputStatus(str, enum.Enum):
    GENERATED = "GENERATED"
    FAILED = "FAILED"
    NOT_CONFIGURED = "NOT_CONFIGURED"


class AIOVStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    GENERATED_FOR_VALIDATOR_REVIEW = "GENERATED_FOR_VALIDATOR_REVIEW"
    SUPERSEDED = "SUPERSEDED"


class AIOutput(Base, TimestampMixin):
    __tablename__ = "ai_outputs"

    id: Mapped[uuid.UUID] = uuid_pk()
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    asset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("assets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    workflow_type: Mapped[WorkflowType] = mapped_column(
        Enum(WorkflowType, name="workflow_type_enum"), nullable=False
    )
    model_provider: Mapped[str] = mapped_column(String(64), nullable=False)
    model_name: Mapped[str] = mapped_column(String(128), nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(64), nullable=False)
    input_reference_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    output_text: Mapped[str | None] = mapped_column(Text)
    output_json: Mapped[dict | None] = mapped_column(JSONB)
    output_sha256: Mapped[str | None] = mapped_column(String(64))
    status: Mapped[AIOutputStatus] = mapped_column(
        Enum(AIOutputStatus, name="ai_output_status_enum"),
        default=AIOutputStatus.GENERATED,
        nullable=False,
    )
    thinking_enabled: Mapped[bool] = mapped_column(default=False, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text)


class AIOVAnalysis(Base, TimestampMixin):
    __tablename__ = "aiov_analyses"

    id: Mapped[uuid.UUID] = uuid_pk()
    asset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("assets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[AIOVStatus] = mapped_column(
        Enum(AIOVStatus, name="aiov_status_enum"),
        default=AIOVStatus.DRAFT,
        nullable=False,
    )
    analysis_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    narrative: Mapped[str | None] = mapped_column(Text)
    supporting_source_ids: Mapped[list[str] | None] = mapped_column(JSONB)
    missing_evidence_json: Mapped[dict | None] = mapped_column(JSONB)
    generated_by_output_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ai_outputs.id", ondelete="SET NULL")
    )
