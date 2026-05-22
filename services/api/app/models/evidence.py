from __future__ import annotations

import enum
import uuid

from sqlalchemy import Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, uuid_pk


class EvidenceType(str, enum.Enum):
    PURCHASE_RECEIPT = "PURCHASE_RECEIPT"
    PRODUCT_SPECIFICATION = "PRODUCT_SPECIFICATION"
    SERIAL_OR_PHOTO = "SERIAL_OR_PHOTO"
    NVIDIA_SMI_CAPTURE = "NVIDIA_SMI_CAPTURE"
    BENCHMARK_OUTPUT = "BENCHMARK_OUTPUT"
    THERMAL_POWER_OUTPUT = "THERMAL_POWER_OUTPUT"
    SYSTEM_SPECIFICATION = "SYSTEM_SPECIFICATION"
    MAINTENANCE_RECORD = "MAINTENANCE_RECORD"
    PRIOR_LISTING = "PRIOR_LISTING"
    OTHER = "OTHER"


class Visibility(str, enum.Enum):
    PRIVATE = "PRIVATE"
    PUBLIC_APPROVED = "PUBLIC_APPROVED"


class IngestionStatus(str, enum.Enum):
    UPLOADED = "UPLOADED"
    HASHING = "HASHING"
    INDEXING = "INDEXING"
    INDEXED = "INDEXED"
    EXTRACTION_FAILED = "EXTRACTION_FAILED"


class ManifestStatus(str, enum.Enum):
    CURRENT = "CURRENT"
    SUPERSEDED = "SUPERSEDED"


class EvidenceItem(Base, TimestampMixin):
    __tablename__ = "evidence_items"

    id: Mapped = uuid_pk()
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    asset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("assets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    filename: Mapped[str] = mapped_column(String(512), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(1024), nullable=False)
    content_type: Mapped[str | None] = mapped_column(String(128))
    byte_size: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    evidence_type: Mapped[EvidenceType] = mapped_column(
        Enum(EvidenceType, name="evidence_type_enum"), nullable=False
    )
    visibility: Mapped[Visibility] = mapped_column(
        Enum(Visibility, name="visibility_enum"),
        default=Visibility.PRIVATE,
        nullable=False,
    )
    ingestion_status: Mapped[IngestionStatus] = mapped_column(
        Enum(IngestionStatus, name="ingestion_status_enum"),
        default=IngestionStatus.UPLOADED,
        nullable=False,
    )
    sha256_hash: Mapped[str | None] = mapped_column(String(64), index=True)
    uploaded_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    provenance: Mapped[str | None] = mapped_column(String(64))  # e.g. USER_UPLOAD, EDGE_CAPTURED
    edge_node_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("edge_nodes.id", ondelete="SET NULL")
    )

    asset = relationship("Asset", back_populates="evidence_items")


class EvidenceManifest(Base, TimestampMixin):
    __tablename__ = "evidence_manifests"

    id: Mapped = uuid_pk()
    asset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("assets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    manifest_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    manifest_sha256: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    status: Mapped[ManifestStatus] = mapped_column(
        Enum(ManifestStatus, name="manifest_status_enum"),
        default=ManifestStatus.CURRENT,
        nullable=False,
    )


class ExtractedDocument(Base, TimestampMixin):
    __tablename__ = "extracted_documents"

    id: Mapped = uuid_pk()
    evidence_item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("evidence_items.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    extraction_status: Mapped[str] = mapped_column(String(32), nullable=False, default="PENDING")
    extracted_text_private: Mapped[str | None] = mapped_column(Text)
    chunk_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    metadata_json: Mapped[dict | None] = mapped_column(JSONB)


class EvidenceChunk(Base, TimestampMixin):
    __tablename__ = "evidence_chunks"

    id: Mapped = uuid_pk()
    evidence_item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("evidence_items.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    asset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("assets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    citation_locator: Mapped[str | None] = mapped_column(String(255))
    metadata_json: Mapped[dict | None] = mapped_column(JSONB)
