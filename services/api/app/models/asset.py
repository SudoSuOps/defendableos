from __future__ import annotations

import enum
import uuid
from datetime import date

from sqlalchemy import (
    Date,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, uuid_pk


class AssetClass(str, enum.Enum):
    COMPUTE_HARDWARE = "COMPUTE_HARDWARE"
    REAL_ESTATE = "REAL_ESTATE"
    EQUIPMENT = "EQUIPMENT"
    LUXURY_GOODS = "LUXURY_GOODS"
    DATASET = "DATASET"
    AI_ASSET = "AI_ASSET"
    OTHER = "OTHER"


class ComputeCategory(str, enum.Enum):
    GPU_ACCELERATOR = "GPU_ACCELERATOR"
    AI_WORKSTATION = "AI_WORKSTATION"
    GPU_SERVER = "GPU_SERVER"
    EDGE_APPLIANCE = "EDGE_APPLIANCE"
    COMPUTE_CLUSTER = "COMPUTE_CLUSTER"
    OTHER = "OTHER"


class IntendedUse(str, enum.Enum):
    INFERENCE = "INFERENCE"
    TRAINING = "TRAINING"
    RENDERING = "RENDERING"
    RENTAL_COMPUTE = "RENTAL_COMPUTE"
    EDGE_INFERENCE = "EDGE_INFERENCE"
    GENERAL_AI_WORKLOAD = "GENERAL_AI_WORKLOAD"


class ConditionStatus(str, enum.Enum):
    NEW = "NEW"
    USED = "USED"
    REFURBISHED = "REFURBISHED"
    UNKNOWN = "UNKNOWN"


class AssetStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    EVIDENCE_INTAKE = "EVIDENCE_INTAKE"
    RESEARCH_IN_PROGRESS = "RESEARCH_IN_PROGRESS"
    AIOV_DRAFTED = "AIOV_DRAFTED"
    VALIDATOR_IN_REVIEW = "VALIDATOR_IN_REVIEW"
    PASSED_FOR_PACKAGING = "PASSED_FOR_PACKAGING"
    DEED_DRAFTED = "DEED_DRAFTED"
    PUBLIC_VERIFICATION_PUBLISHED = "PUBLIC_VERIFICATION_PUBLISHED"
    ARCHIVED = "ARCHIVED"


class Asset(Base, TimestampMixin):
    __tablename__ = "assets"
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "public_asset_reference",
            name="uq_asset_org_public_ref",
        ),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    public_asset_reference: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    asset_class: Mapped[AssetClass] = mapped_column(Enum(AssetClass, name="asset_class_enum"), nullable=False)
    category: Mapped[str | None] = mapped_column(String(64))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[AssetStatus] = mapped_column(
        Enum(AssetStatus, name="asset_status_enum"),
        default=AssetStatus.DRAFT,
        nullable=False,
    )
    private_serial_number: Mapped[str | None] = mapped_column(String(255))
    client_internal_reference: Mapped[str | None] = mapped_column(String(255))
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )

    organization = relationship("Organization", back_populates="assets")
    compute_profile = relationship(
        "ComputeAssetProfile",
        back_populates="asset",
        uselist=False,
        cascade="all, delete-orphan",
    )
    evidence_items = relationship(
        "EvidenceItem", back_populates="asset", cascade="all, delete-orphan"
    )
    deeds = relationship("DefendableDeed", back_populates="asset", cascade="all, delete-orphan")


class ComputeAssetProfile(Base, TimestampMixin):
    __tablename__ = "compute_asset_profiles"

    id: Mapped[uuid.UUID] = uuid_pk()
    asset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("assets.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    manufacturer: Mapped[str | None] = mapped_column(String(128))
    model: Mapped[str | None] = mapped_column(String(255))
    gpu_count: Mapped[int | None] = mapped_column(Integer)
    vram_per_gpu_gb: Mapped[int | None] = mapped_column(Integer)
    cpu: Mapped[str | None] = mapped_column(String(255))
    ram_gb: Mapped[int | None] = mapped_column(Integer)
    storage_description: Mapped[str | None] = mapped_column(Text)
    networking_description: Mapped[str | None] = mapped_column(Text)
    operating_system: Mapped[str | None] = mapped_column(String(128))
    condition_status: Mapped[ConditionStatus | None] = mapped_column(
        Enum(ConditionStatus, name="condition_status_enum")
    )
    operational_status: Mapped[str | None] = mapped_column(String(128))
    intended_use: Mapped[IntendedUse | None] = mapped_column(
        Enum(IntendedUse, name="intended_use_enum")
    )
    purchase_date: Mapped[date | None] = mapped_column(Date)
    purchase_cost_private: Mapped[float | None] = mapped_column(Numeric(14, 2))

    asset = relationship("Asset", back_populates="compute_profile")
