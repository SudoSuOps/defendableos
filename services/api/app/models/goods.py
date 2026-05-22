"""Defendable Goods Intelligence · domain models.

Adds 15 new tables that power the Goods Vault, Trend Discovery, Comp
Foundry, Pair Factory, Source Rights ledger, MarketReady linkage, and
the cross-cutting ArtifactRegistry. All models extend the existing
SQLAlchemy declarative base · NONE of the existing user / organization
/ asset / evidence / deed / validator tables are modified.

Doctrine encoded directly in the schema:
  · TrendSignal.comp_eligibility is FROZEN at NOT_A_COMP at the
    application layer (DB allows the column, but services refuse to
    persist anything else · see app/services/comp_foundry.py).
  · MarketObservation enforces transaction_confirmed=false for any
    PUBLIC_ACTIVE_LISTING source_type (constraint check at the
    service layer · see comp_foundry.py).
  · SourceRightsRecord defaults all third-party-derived data to
    INTERNAL_RESEARCH_ONLY with training_eligible=False and
    public_display_eligible=False.
  · TrainingPair defaults to CANDIDATE_ONLY · training_eligible=False
    until a SourceRightsRecord with TRAINING_ALLOWED is attached AND
    a validator review approves the batch.
  · ApprovedClaim is the ONLY mechanism by which a fact may flow to
    a public MarketReady surface · everything else is blocked.

This file is intentionally one module · the next migration creates
the matching 15 tables atomically. Future expansion (luxury,
collectibles, CRE) reuses the same goods_class enum extension.
"""
from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, uuid_pk


# ────────────────────────────────────────────────────────────────────
#  ENUMS · stable strings · safe to add values, never remove
# ────────────────────────────────────────────────────────────────────


class GoodsClass(str, enum.Enum):
    COMPUTE_HARDWARE = "COMPUTE_HARDWARE"
    LUXURY_GOOD = "LUXURY_GOOD"
    EQUIPMENT = "EQUIPMENT"
    COLLECTIBLE = "COLLECTIBLE"
    CONSUMER_ELECTRONICS = "CONSUMER_ELECTRONICS"
    DATASET = "DATASET"
    AI_ASSET = "AI_ASSET"
    OTHER = "OTHER"


class IdentityStatus(str, enum.Enum):
    NORMALIZED_PENDING_REVIEW = "NORMALIZED_PENDING_REVIEW"
    REVIEWED = "REVIEWED"
    CONFLICT_DETECTED = "CONFLICT_DETECTED"


class IdentifierType(str, enum.Enum):
    INTERNAL = "INTERNAL"
    GTIN = "GTIN"
    EPID = "EPID"
    MPN = "MPN"
    SKU = "SKU"
    SERIAL_REDACTED_REFERENCE = "SERIAL_REDACTED_REFERENCE"
    OTHER = "OTHER"


class ProviderName(str, enum.Enum):
    BRAVE_LLM_CONTEXT = "BRAVE_LLM_CONTEXT"
    EBAY_BROWSE = "EBAY_BROWSE"
    EBAY_INVENTORY = "EBAY_INVENTORY"
    SHOPIFY_FUTURE = "SHOPIFY_FUTURE"
    CLIENT_UPLOAD = "CLIENT_UPLOAD"
    FIRST_PARTY_TRANSACTION = "FIRST_PARTY_TRANSACTION"
    LICENSED_TRANSACTION_DATA_FUTURE = "LICENSED_TRANSACTION_DATA_FUTURE"


class ProviderStatus(str, enum.Enum):
    NOT_CONFIGURED = "NOT_CONFIGURED"
    CONFIGURED_DISABLED = "CONFIGURED_DISABLED"
    READY = "READY"
    ERROR = "ERROR"
    FUTURE_DISABLED = "FUTURE_DISABLED"


class TermsReviewStatus(str, enum.Enum):
    TERMS_REVIEW_PENDING = "TERMS_REVIEW_PENDING"
    REVIEWED_INTERNAL_RESEARCH_ONLY = "REVIEWED_INTERNAL_RESEARCH_ONLY"
    REVIEWED_EVAL_ALLOWED = "REVIEWED_EVAL_ALLOWED"
    REVIEWED_TRAINING_ALLOWED = "REVIEWED_TRAINING_ALLOWED"
    RESTRICTED_DO_NOT_USE = "RESTRICTED_DO_NOT_USE"


class RunType(str, enum.Enum):
    TREND_DISCOVERY = "TREND_DISCOVERY"
    MARKET_CONTEXT_RESEARCH = "MARKET_CONTEXT_RESEARCH"
    ACTIVE_LISTING_SEARCH = "ACTIVE_LISTING_SEARCH"


class RunStatus(str, enum.Enum):
    CREATED = "CREATED"
    MOCK_COMPLETED = "MOCK_COMPLETED"
    LIVE_COMPLETED = "LIVE_COMPLETED"
    PROVIDER_DISABLED = "PROVIDER_DISABLED"
    ERROR = "ERROR"


class SignalStrength(str, enum.Enum):
    WATCHLIST = "WATCHLIST"
    DISCOVERY = "DISCOVERY"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    REJECTED = "REJECTED"


class SourceType(str, enum.Enum):
    PUBLIC_ACTIVE_LISTING = "PUBLIC_ACTIVE_LISTING"
    MANUFACTURER_SPECIFICATION = "MANUFACTURER_SPECIFICATION"
    PUBLIC_MARKET_CONTEXT = "PUBLIC_MARKET_CONTEXT"
    FIRST_PARTY_TRANSACTION = "FIRST_PARTY_TRANSACTION"
    LICENSED_TRANSACTION_DATA = "LICENSED_TRANSACTION_DATA"
    CLIENT_PROVIDED_SALE_RECEIPT = "CLIENT_PROVIDED_SALE_RECEIPT"
    FOUNDER_OWNED_VERIFIED_SALE = "FOUNDER_OWNED_VERIFIED_SALE"
    AUTHORIZED_MERCHANT_TRANSACTION = "AUTHORIZED_MERCHANT_TRANSACTION"


class PriceType(str, enum.Enum):
    ASKING_PRICE = "ASKING_PRICE"
    CONFIRMED_TRANSACTION_PRICE = "CONFIRMED_TRANSACTION_PRICE"
    UNKNOWN = "UNKNOWN"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class CompEligibility(str, enum.Enum):
    NOT_A_COMP = "NOT_A_COMP"
    CANDIDATE_ONLY = "CANDIDATE_ONLY"
    MARKET_CONTEXT_ONLY = "MARKET_CONTEXT_ONLY"
    ELIGIBLE_AFTER_REVIEW = "ELIGIBLE_AFTER_REVIEW"


class CompQualityGrade(str, enum.Enum):
    """A: confirmed transaction · high attribute match.
    B: authorized transaction · review limitations.
    C: active listing · high identity match · asking-market context only.
    D: weak listing · discovery only.
    E: trend signal · never comp evidence.
    """
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    E = "E"


class TransactionStatus(str, enum.Enum):
    RECEIVED_PENDING_REVIEW = "RECEIVED_PENDING_REVIEW"
    CONFIRMED_WITH_EVIDENCE = "CONFIRMED_WITH_EVIDENCE"
    REJECTED_INSUFFICIENT_EVIDENCE = "REJECTED_INSUFFICIENT_EVIDENCE"


class PrivacyClass(str, enum.Enum):
    PRIVATE_BY_DEFAULT = "PRIVATE_BY_DEFAULT"
    APPROVED_DERIVATIVE_ONLY = "APPROVED_DERIVATIVE_ONLY"
    PUBLIC_SAFE_APPROVED = "PUBLIC_SAFE_APPROVED"


class CompSetIntendedUse(str, enum.Enum):
    MARKET_CONTEXT_RESEARCH = "MARKET_CONTEXT_RESEARCH"
    AIOV_DRAFT_INPUT = "AIOV_DRAFT_INPUT"
    MARKETREADY_POSITIONING = "MARKETREADY_POSITIONING"
    VALUE_SUPPORT_REVIEW = "VALUE_SUPPORT_REVIEW"


class CompSetStatus(str, enum.Enum):
    DRAFT_RESEARCH = "DRAFT_RESEARCH"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    NOT_READY_FOR_VALUE_SUPPORT = "NOT_READY_FOR_VALUE_SUPPORT"
    READY_FOR_DRAFT_ANALYSIS = "READY_FOR_DRAFT_ANALYSIS"
    APPROVED_FOR_LIMITED_USE = "APPROVED_FOR_LIMITED_USE"


class RightsStatus(str, enum.Enum):
    TERMS_REVIEW_PENDING = "TERMS_REVIEW_PENDING"
    INTERNAL_RESEARCH_ONLY = "INTERNAL_RESEARCH_ONLY"
    EVAL_DERIVATIVE_ALLOWED = "EVAL_DERIVATIVE_ALLOWED"
    TRAINING_ALLOWED = "TRAINING_ALLOWED"
    PUBLIC_DISPLAY_ALLOWED = "PUBLIC_DISPLAY_ALLOWED"
    RESTRICTED_DO_NOT_EXPORT = "RESTRICTED_DO_NOT_EXPORT"


class PairBatchType(str, enum.Enum):
    IDENTITY_NORMALIZATION = "IDENTITY_NORMALIZATION"
    LISTING_VS_TRANSACTION_CLASSIFICATION = "LISTING_VS_TRANSACTION_CLASSIFICATION"
    COMP_QUALITY_GRADING = "COMP_QUALITY_GRADING"
    UNSUPPORTED_VALUE_CLAIM_DETECTION = "UNSUPPORTED_VALUE_CLAIM_DETECTION"
    EVIDENCE_SUFFICIENCY_REVIEW = "EVIDENCE_SUFFICIENCY_REVIEW"
    VALUE_RANGE_WITHHOLDING = "VALUE_RANGE_WITHHOLDING"
    MARKETREADY_CLAIM_PERMISSION = "MARKETREADY_CLAIM_PERMISSION"


class PairBatchStatus(str, enum.Enum):
    DRAFT_CANDIDATES = "DRAFT_CANDIDATES"
    READY_FOR_VALIDATOR = "READY_FOR_VALIDATOR"
    APPROVED_FOR_EVAL = "APPROVED_FOR_EVAL"
    APPROVED_FOR_TRAINING = "APPROVED_FOR_TRAINING"
    REJECTED = "REJECTED"


class TrainingPairUseClass(str, enum.Enum):
    CANDIDATE_ONLY = "CANDIDATE_ONLY"
    EVAL_ONLY = "EVAL_ONLY"
    TRAINING_ELIGIBLE = "TRAINING_ELIGIBLE"


class PublicClaimPermission(str, enum.Enum):
    PUBLIC_SAFE_APPROVED = "PUBLIC_SAFE_APPROVED"
    PUBLIC_SAFE_WITH_REQUIRED_DISCLOSURE = "PUBLIC_SAFE_WITH_REQUIRED_DISCLOSURE"
    INTERNAL_ONLY = "INTERNAL_ONLY"
    BLOCKED_FROM_PUBLIC_MARKETING = "BLOCKED_FROM_PUBLIC_MARKETING"


class MarketReadyPackageStatus(str, enum.Enum):
    NOT_READY = "NOT_READY"
    DRAFT_INPUTS_READY = "DRAFT_INPUTS_READY"
    APPROVED_CLAIMS_READY = "APPROVED_CLAIMS_READY"
    EXPORT_BLOCKED = "EXPORT_BLOCKED"


class ArtifactType(str, enum.Enum):
    PROVIDER_RAW_RESPONSE = "PROVIDER_RAW_RESPONSE"
    NORMALIZED_OBSERVATION_BATCH = "NORMALIZED_OBSERVATION_BATCH"
    NORMALIZED_TREND_SIGNAL_BATCH = "NORMALIZED_TREND_SIGNAL_BATCH"
    COMP_SET_RECEIPT = "COMP_SET_RECEIPT"
    PAIR_CANDIDATES_JSONL = "PAIR_CANDIDATES_JSONL"
    PAIR_APPROVED_EVAL_JSONL = "PAIR_APPROVED_EVAL_JSONL"
    PAIR_APPROVED_TRAINING_JSONL = "PAIR_APPROVED_TRAINING_JSONL"
    DATASET_MANIFEST = "DATASET_MANIFEST"
    DATASET_SHA256SUMS = "DATASET_SHA256SUMS"
    PUBLIC_DEED_PREVIEW = "PUBLIC_DEED_PREVIEW"
    MARKETREADY_MEDIA = "MARKETREADY_MEDIA"


class ArtifactPrivacyClass(str, enum.Enum):
    PRIVATE_EVIDENCE = "PRIVATE_EVIDENCE"
    MARKET_OBSERVATIONS = "MARKET_OBSERVATIONS"
    DERIVED_DATASETS = "DERIVED_DATASETS"
    PUBLIC_ASSETS = "PUBLIC_ASSETS"


# ────────────────────────────────────────────────────────────────────
#  1 · SourceConnector · the cross-cutting provider registry
# ────────────────────────────────────────────────────────────────────


class SourceConnector(Base, TimestampMixin):
    __tablename__ = "source_connectors"

    id: Mapped[uuid.UUID] = uuid_pk()
    provider_name: Mapped[ProviderName] = mapped_column(
        Enum(ProviderName, name="provider_name_enum"), nullable=False, unique=True, index=True
    )
    connector_purpose: Mapped[str] = mapped_column(String(255), nullable=False)
    provider_status: Mapped[ProviderStatus] = mapped_column(
        Enum(ProviderStatus, name="provider_status_enum"),
        nullable=False,
        default=ProviderStatus.NOT_CONFIGURED,
    )
    live_calls_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    terms_review_status: Mapped[TermsReviewStatus] = mapped_column(
        Enum(TermsReviewStatus, name="terms_review_status_enum"),
        nullable=False,
        default=TermsReviewStatus.TERMS_REVIEW_PENDING,
    )
    last_health_check_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_error_message: Mapped[str | None] = mapped_column(Text)


# ────────────────────────────────────────────────────────────────────
#  2 · DiscoveryRun · one row per controlled provider call
# ────────────────────────────────────────────────────────────────────


class DiscoveryRun(Base, TimestampMixin):
    __tablename__ = "discovery_runs"

    id: Mapped[uuid.UUID] = uuid_pk()
    run_id: Mapped[str] = mapped_column(String(80), unique=True, index=True, nullable=False)
    provider: Mapped[ProviderName] = mapped_column(
        Enum(ProviderName, name="provider_name_enum"), nullable=False, index=True
    )
    run_type: Mapped[RunType] = mapped_column(
        Enum(RunType, name="run_type_enum"), nullable=False
    )
    query: Mapped[str] = mapped_column(Text, nullable=False)
    goods_class: Mapped[GoodsClass | None] = mapped_column(
        Enum(GoodsClass, name="goods_class_enum")
    )
    category: Mapped[str | None] = mapped_column(String(120))
    status: Mapped[RunStatus] = mapped_column(
        Enum(RunStatus, name="run_status_enum"), nullable=False, default=RunStatus.CREATED
    )
    raw_artifact_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("artifact_registry.id", ondelete="SET NULL")
    )
    normalized_artifact_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("artifact_registry.id", ondelete="SET NULL")
    )
    raw_sha256: Mapped[str | None] = mapped_column(String(64))
    normalized_sha256: Mapped[str | None] = mapped_column(String(64))
    error_message: Mapped[str | None] = mapped_column(Text)
    initiated_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


# ────────────────────────────────────────────────────────────────────
#  3 · TrendSignal · NEVER a comp · grade always E
# ────────────────────────────────────────────────────────────────────


class TrendSignal(Base, TimestampMixin):
    __tablename__ = "trend_signals"

    id: Mapped[uuid.UUID] = uuid_pk()
    discovery_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("discovery_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    signal_name: Mapped[str] = mapped_column(String(255), nullable=False)
    goods_class: Mapped[GoodsClass] = mapped_column(
        Enum(GoodsClass, name="goods_class_enum"), nullable=False
    )
    category: Mapped[str | None] = mapped_column(String(120))
    manufacturer: Mapped[str | None] = mapped_column(String(120))
    model: Mapped[str | None] = mapped_column(String(255))
    signal_strength: Mapped[SignalStrength] = mapped_column(
        Enum(SignalStrength, name="signal_strength_enum"),
        nullable=False,
        default=SignalStrength.DISCOVERY,
    )
    classification: Mapped[str] = mapped_column(
        String(32), nullable=False, default="TREND_SIGNAL"
    )
    comp_eligibility: Mapped[CompEligibility] = mapped_column(
        Enum(CompEligibility, name="comp_eligibility_enum"),
        nullable=False,
        default=CompEligibility.NOT_A_COMP,
    )
    evidence_basis: Mapped[str | None] = mapped_column(Text)
    recommended_market_query: Mapped[str | None] = mapped_column(Text)
    source_limitations: Mapped[dict] = mapped_column(JSONB, nullable=False, default=list)


# ────────────────────────────────────────────────────────────────────
#  4 · CanonicalGood · normalized identity for a watchable product
# ────────────────────────────────────────────────────────────────────


class CanonicalGood(Base, TimestampMixin):
    __tablename__ = "canonical_goods"

    id: Mapped[uuid.UUID] = uuid_pk()
    goods_id: Mapped[str] = mapped_column(String(120), unique=True, nullable=False, index=True)
    goods_class: Mapped[GoodsClass] = mapped_column(
        Enum(GoodsClass, name="goods_class_enum"), nullable=False, index=True
    )
    category: Mapped[str | None] = mapped_column(String(120))
    manufacturer: Mapped[str | None] = mapped_column(String(120))
    model: Mapped[str | None] = mapped_column(String(255))
    canonical_title: Mapped[str] = mapped_column(String(500), nullable=False)
    normalized_attributes: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    identity_status: Mapped[IdentityStatus] = mapped_column(
        Enum(IdentityStatus, name="goods_identity_status_enum"),
        nullable=False,
        default=IdentityStatus.NORMALIZED_PENDING_REVIEW,
    )
    primary_asset_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("assets.id", ondelete="SET NULL")
    )
    # Embedding · prepared for pgvector when enabled. JSONB list for now to
    # avoid hard pgvector dependency in dev. Service layer can copy into a
    # vector column when pgvector is enabled in production.
    embedding_json: Mapped[list | None] = mapped_column(JSONB)


# ────────────────────────────────────────────────────────────────────
#  5 · GoodsIdentifier · GTIN / EPID / MPN / SKU per good
# ────────────────────────────────────────────────────────────────────


class GoodsIdentifier(Base, TimestampMixin):
    __tablename__ = "goods_identifiers"

    id: Mapped[uuid.UUID] = uuid_pk()
    goods_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("canonical_goods.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    identifier_type: Mapped[IdentifierType] = mapped_column(
        Enum(IdentifierType, name="identifier_type_enum"), nullable=False
    )
    identifier_value: Mapped[str] = mapped_column(String(255), nullable=False)
    source_provider: Mapped[ProviderName | None] = mapped_column(
        Enum(ProviderName, name="provider_name_enum")
    )
    disclosure_class: Mapped[PublicClaimPermission] = mapped_column(
        Enum(PublicClaimPermission, name="public_claim_permission_enum"),
        nullable=False,
        default=PublicClaimPermission.INTERNAL_ONLY,
    )
    review_status: Mapped[IdentityStatus] = mapped_column(
        Enum(IdentityStatus, name="goods_identity_status_enum"),
        nullable=False,
        default=IdentityStatus.NORMALIZED_PENDING_REVIEW,
    )


# ────────────────────────────────────────────────────────────────────
#  6 · MarketObservation · single public listing or context entry
# ────────────────────────────────────────────────────────────────────


class MarketObservation(Base, TimestampMixin):
    __tablename__ = "market_observations"

    id: Mapped[uuid.UUID] = uuid_pk()
    observation_id: Mapped[str] = mapped_column(String(120), unique=True, nullable=False, index=True)
    goods_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("canonical_goods.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    discovery_run_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("discovery_runs.id", ondelete="SET NULL")
    )
    source_provider: Mapped[ProviderName] = mapped_column(
        Enum(ProviderName, name="provider_name_enum"), nullable=False
    )
    source_type: Mapped[SourceType] = mapped_column(
        Enum(SourceType, name="source_type_enum"), nullable=False
    )
    source_reference: Mapped[str | None] = mapped_column(Text)
    title_raw: Mapped[str | None] = mapped_column(Text)
    title_normalized: Mapped[str | None] = mapped_column(Text)
    observed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    condition_claimed: Mapped[str | None] = mapped_column(String(64))
    price_amount: Mapped[float | None] = mapped_column(Numeric(14, 2))
    price_currency: Mapped[str | None] = mapped_column(String(3))
    price_type: Mapped[PriceType] = mapped_column(
        Enum(PriceType, name="price_type_enum"), nullable=False, default=PriceType.UNKNOWN
    )
    transaction_confirmed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    item_location_summary: Mapped[str | None] = mapped_column(String(255))
    listing_status: Mapped[str | None] = mapped_column(String(64))
    image_reference_policy: Mapped[str | None] = mapped_column(String(64))
    identity_match_score: Mapped[float | None] = mapped_column(Float)
    comp_eligibility: Mapped[CompEligibility] = mapped_column(
        Enum(CompEligibility, name="comp_eligibility_enum"),
        nullable=False,
        default=CompEligibility.CANDIDATE_ONLY,
    )
    comp_quality_grade: Mapped[CompQualityGrade | None] = mapped_column(
        Enum(CompQualityGrade, name="comp_quality_grade_enum")
    )
    limitations: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    rights_status: Mapped[RightsStatus] = mapped_column(
        Enum(RightsStatus, name="rights_status_enum"),
        nullable=False,
        default=RightsStatus.INTERNAL_RESEARCH_ONLY,
    )
    raw_artifact_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("artifact_registry.id", ondelete="SET NULL")
    )
    normalized_sha256: Mapped[str | None] = mapped_column(String(64))


# ────────────────────────────────────────────────────────────────────
#  7 · TransactionEvidence · confirmed sale records
# ────────────────────────────────────────────────────────────────────


class TransactionEvidence(Base, TimestampMixin):
    __tablename__ = "transaction_evidences"

    id: Mapped[uuid.UUID] = uuid_pk()
    transaction_id: Mapped[str] = mapped_column(String(120), unique=True, nullable=False, index=True)
    goods_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("canonical_goods.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    asset_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("assets.id", ondelete="SET NULL")
    )
    source_type: Mapped[SourceType] = mapped_column(
        Enum(SourceType, name="source_type_enum"), nullable=False
    )
    transaction_status: Mapped[TransactionStatus] = mapped_column(
        Enum(TransactionStatus, name="transaction_status_enum"),
        nullable=False,
        default=TransactionStatus.RECEIVED_PENDING_REVIEW,
    )
    sale_price_amount: Mapped[float | None] = mapped_column(Numeric(14, 2))
    sale_price_currency: Mapped[str | None] = mapped_column(String(3))
    transaction_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    evidence_manifest_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("evidence_manifests.id", ondelete="SET NULL")
    )
    privacy_class: Mapped[PrivacyClass] = mapped_column(
        Enum(PrivacyClass, name="privacy_class_enum"),
        nullable=False,
        default=PrivacyClass.PRIVATE_BY_DEFAULT,
    )
    rights_status: Mapped[RightsStatus] = mapped_column(
        Enum(RightsStatus, name="rights_status_enum"),
        nullable=False,
        default=RightsStatus.TERMS_REVIEW_PENDING,
    )
    training_permission: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    validator_receipt_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("validator_reviews.id", ondelete="SET NULL")
    )


# ────────────────────────────────────────────────────────────────────
#  8 · CompSet · graded comparable set
# ────────────────────────────────────────────────────────────────────


class CompSet(Base, TimestampMixin):
    __tablename__ = "comp_sets"

    id: Mapped[uuid.UUID] = uuid_pk()
    comp_set_id: Mapped[str] = mapped_column(String(120), unique=True, nullable=False, index=True)
    goods_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("canonical_goods.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    asset_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("assets.id", ondelete="SET NULL")
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    intended_use: Mapped[CompSetIntendedUse] = mapped_column(
        Enum(CompSetIntendedUse, name="comp_set_intended_use_enum"),
        nullable=False,
        default=CompSetIntendedUse.MARKET_CONTEXT_RESEARCH,
    )
    comp_set_status: Mapped[CompSetStatus] = mapped_column(
        Enum(CompSetStatus, name="comp_set_status_enum"),
        nullable=False,
        default=CompSetStatus.DRAFT_RESEARCH,
    )
    grade_summary: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    limitations: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    confirmed_transaction_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    active_listing_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    trend_signal_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    validator_status: Mapped[str | None] = mapped_column(String(64))


# ────────────────────────────────────────────────────────────────────
#  9 · CompSetMember · one row per observation/transaction in a comp set
# ────────────────────────────────────────────────────────────────────


class CompSetMember(Base, TimestampMixin):
    __tablename__ = "comp_set_members"

    id: Mapped[uuid.UUID] = uuid_pk()
    comp_set_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("comp_sets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    observation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("market_observations.id", ondelete="CASCADE")
    )
    transaction_evidence_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("transaction_evidences.id", ondelete="CASCADE")
    )
    trend_signal_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("trend_signals.id", ondelete="CASCADE")
    )
    quality_grade: Mapped[CompQualityGrade] = mapped_column(
        Enum(CompQualityGrade, name="comp_quality_grade_enum"), nullable=False
    )
    inclusion_reason: Mapped[str | None] = mapped_column(Text)
    limitations: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    included_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )


# ────────────────────────────────────────────────────────────────────
#  10 · SourceRightsRecord · per-source training/display rights
# ────────────────────────────────────────────────────────────────────


class SourceRightsRecord(Base, TimestampMixin):
    __tablename__ = "source_rights_records"

    id: Mapped[uuid.UUID] = uuid_pk()
    source_connector_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("source_connectors.id", ondelete="SET NULL")
    )
    artifact_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("artifact_registry.id", ondelete="SET NULL")
    )
    data_class: Mapped[str] = mapped_column(String(64), nullable=False)
    acquisition_method: Mapped[str] = mapped_column(String(64), nullable=False)
    rights_status: Mapped[RightsStatus] = mapped_column(
        Enum(RightsStatus, name="rights_status_enum"),
        nullable=False,
        default=RightsStatus.INTERNAL_RESEARCH_ONLY,
    )
    training_eligible: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    public_display_eligible: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    retention_policy: Mapped[str | None] = mapped_column(String(120))
    review_notes: Mapped[str | None] = mapped_column(Text)
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


# ────────────────────────────────────────────────────────────────────
#  11 · PairBatch · receipts-bound pair candidate batches
# ────────────────────────────────────────────────────────────────────


class PairBatch(Base, TimestampMixin):
    __tablename__ = "pair_batches"

    id: Mapped[uuid.UUID] = uuid_pk()
    batch_id: Mapped[str] = mapped_column(String(120), unique=True, nullable=False, index=True)
    goods_class: Mapped[GoodsClass] = mapped_column(
        Enum(GoodsClass, name="goods_class_enum"), nullable=False
    )
    batch_type: Mapped[PairBatchType] = mapped_column(
        Enum(PairBatchType, name="pair_batch_type_enum"), nullable=False
    )
    batch_status: Mapped[PairBatchStatus] = mapped_column(
        Enum(PairBatchStatus, name="pair_batch_status_enum"),
        nullable=False,
        default=PairBatchStatus.DRAFT_CANDIDATES,
    )
    source_rights_status: Mapped[RightsStatus] = mapped_column(
        Enum(RightsStatus, name="rights_status_enum"),
        nullable=False,
        default=RightsStatus.INTERNAL_RESEARCH_ONLY,
    )
    validator_status: Mapped[str | None] = mapped_column(String(64))
    training_eligible: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    manifest_artifact_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("artifact_registry.id", ondelete="SET NULL")
    )
    manifest_sha256: Mapped[str | None] = mapped_column(String(64))


# ────────────────────────────────────────────────────────────────────
#  12 · TrainingPair · individual candidate pair
# ────────────────────────────────────────────────────────────────────


class TrainingPair(Base, TimestampMixin):
    __tablename__ = "training_pairs"

    id: Mapped[uuid.UUID] = uuid_pk()
    pair_id: Mapped[str] = mapped_column(String(120), unique=True, nullable=False, index=True)
    pair_batch_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("pair_batches.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    goods_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("canonical_goods.id", ondelete="SET NULL")
    )
    pair_type: Mapped[PairBatchType] = mapped_column(
        Enum(PairBatchType, name="pair_batch_type_enum"), nullable=False
    )
    source_lineage: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    input_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    expected_output_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    validator_status: Mapped[str] = mapped_column(
        String(64), nullable=False, default="VALIDATOR_REVIEW_REQUIRED"
    )
    source_rights_status: Mapped[RightsStatus] = mapped_column(
        Enum(RightsStatus, name="rights_status_enum"),
        nullable=False,
        default=RightsStatus.INTERNAL_RESEARCH_ONLY,
    )
    use_class: Mapped[TrainingPairUseClass] = mapped_column(
        Enum(TrainingPairUseClass, name="training_pair_use_class_enum"),
        nullable=False,
        default=TrainingPairUseClass.CANDIDATE_ONLY,
    )
    training_eligible: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    artifact_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("artifact_registry.id", ondelete="SET NULL")
    )
    sha256: Mapped[str | None] = mapped_column(String(64))


# ────────────────────────────────────────────────────────────────────
#  13 · ApprovedClaim · gateway to public marketing surfaces
# ────────────────────────────────────────────────────────────────────


class ApprovedClaim(Base, TimestampMixin):
    __tablename__ = "approved_claims"

    id: Mapped[uuid.UUID] = uuid_pk()
    asset_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("assets.id", ondelete="CASCADE")
    )
    goods_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("canonical_goods.id", ondelete="SET NULL")
    )
    claim_text: Mapped[str] = mapped_column(Text, nullable=False)
    claim_type: Mapped[str] = mapped_column(String(64), nullable=False)
    source_lineage: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    validator_status: Mapped[str | None] = mapped_column(String(64))
    public_permission: Mapped[PublicClaimPermission] = mapped_column(
        Enum(PublicClaimPermission, name="public_claim_permission_enum"),
        nullable=False,
        default=PublicClaimPermission.INTERNAL_ONLY,
    )
    required_disclosure: Mapped[str | None] = mapped_column(Text)
    applicable_surfaces: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)


# ────────────────────────────────────────────────────────────────────
#  14 · MarketReadyDataLink · join between asset and goods intelligence
# ────────────────────────────────────────────────────────────────────


class MarketReadyDataLink(Base, TimestampMixin):
    __tablename__ = "marketready_data_links"

    id: Mapped[uuid.UUID] = uuid_pk()
    asset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("assets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    goods_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("canonical_goods.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    comp_set_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("comp_sets.id", ondelete="SET NULL")
    )
    approved_claim_ids: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    package_status: Mapped[MarketReadyPackageStatus] = mapped_column(
        Enum(MarketReadyPackageStatus, name="marketready_package_status_enum"),
        nullable=False,
        default=MarketReadyPackageStatus.NOT_READY,
    )


# ────────────────────────────────────────────────────────────────────
#  15 · ArtifactRegistry · the universal object-storage index
# ────────────────────────────────────────────────────────────────────


class ArtifactRegistry(Base, TimestampMixin):
    __tablename__ = "artifact_registry"

    id: Mapped[uuid.UUID] = uuid_pk()
    bucket: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    object_key: Mapped[str] = mapped_column(String(500), nullable=False)
    artifact_type: Mapped[ArtifactType] = mapped_column(
        Enum(ArtifactType, name="artifact_type_enum"), nullable=False
    )
    privacy_class: Mapped[ArtifactPrivacyClass] = mapped_column(
        Enum(ArtifactPrivacyClass, name="artifact_privacy_class_enum"), nullable=False
    )
    owner_organization_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="SET NULL")
    )
    asset_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("assets.id", ondelete="SET NULL")
    )
    goods_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("canonical_goods.id", ondelete="SET NULL")
    )
    discovery_run_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("discovery_runs.id", ondelete="SET NULL")
    )
    pair_batch_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("pair_batches.id", ondelete="SET NULL")
    )
    sha256: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    mime_type: Mapped[str | None] = mapped_column(String(120))
    byte_size: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    rights_status: Mapped[RightsStatus] = mapped_column(
        Enum(RightsStatus, name="rights_status_enum"),
        nullable=False,
        default=RightsStatus.INTERNAL_RESEARCH_ONLY,
    )
    retention_policy: Mapped[str | None] = mapped_column(String(120))


__all__ = [
    # enums
    "GoodsClass",
    "IdentityStatus",
    "IdentifierType",
    "ProviderName",
    "ProviderStatus",
    "TermsReviewStatus",
    "RunType",
    "RunStatus",
    "SignalStrength",
    "SourceType",
    "PriceType",
    "CompEligibility",
    "CompQualityGrade",
    "TransactionStatus",
    "PrivacyClass",
    "CompSetIntendedUse",
    "CompSetStatus",
    "RightsStatus",
    "PairBatchType",
    "PairBatchStatus",
    "TrainingPairUseClass",
    "PublicClaimPermission",
    "MarketReadyPackageStatus",
    "ArtifactType",
    "ArtifactPrivacyClass",
    # models
    "SourceConnector",
    "DiscoveryRun",
    "TrendSignal",
    "CanonicalGood",
    "GoodsIdentifier",
    "MarketObservation",
    "TransactionEvidence",
    "CompSet",
    "CompSetMember",
    "SourceRightsRecord",
    "PairBatch",
    "TrainingPair",
    "ApprovedClaim",
    "MarketReadyDataLink",
    "ArtifactRegistry",
]
