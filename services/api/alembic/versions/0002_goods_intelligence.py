"""goods intelligence schema · vault + comp foundry + pair factory

Revision ID: 0002_goods_intelligence
Revises: 0001_initial
Create Date: 2026-05-22

Adds 15 tables for the Goods Vault, Trend Discovery, Comp Foundry,
Pair Factory, Source Rights ledger, MarketReady linkage, and the
universal ArtifactRegistry. No existing tables are modified · this
migration is purely additive.

Enums are created explicitly first (CREATE TYPE) so SQLAlchemy's
ENUM(..., create_type=False) declarations in the table DDL never
attempt re-creation.
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0002_goods_intelligence"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


# New enums introduced by this migration. Names chosen to avoid
# colliding with the 0001 baseline (e.g. goods_identity_status_enum
# avoids the existing identity_status_enum used by ENS).
ENUMS: dict[str, tuple[str, ...]] = {
    "goods_class_enum": (
        "COMPUTE_HARDWARE", "LUXURY_GOOD", "EQUIPMENT", "COLLECTIBLE",
        "CONSUMER_ELECTRONICS", "DATASET", "AI_ASSET", "OTHER",
    ),
    "goods_identity_status_enum": (
        "NORMALIZED_PENDING_REVIEW", "REVIEWED", "CONFLICT_DETECTED",
    ),
    "identifier_type_enum": (
        "INTERNAL", "GTIN", "EPID", "MPN", "SKU",
        "SERIAL_REDACTED_REFERENCE", "OTHER",
    ),
    "provider_name_enum": (
        "BRAVE_LLM_CONTEXT", "EBAY_BROWSE", "EBAY_INVENTORY",
        "SHOPIFY_FUTURE", "CLIENT_UPLOAD", "FIRST_PARTY_TRANSACTION",
        "LICENSED_TRANSACTION_DATA_FUTURE",
    ),
    "provider_status_enum": (
        "NOT_CONFIGURED", "CONFIGURED_DISABLED", "READY", "ERROR",
        "FUTURE_DISABLED",
    ),
    "terms_review_status_enum": (
        "TERMS_REVIEW_PENDING", "REVIEWED_INTERNAL_RESEARCH_ONLY",
        "REVIEWED_EVAL_ALLOWED", "REVIEWED_TRAINING_ALLOWED",
        "RESTRICTED_DO_NOT_USE",
    ),
    "run_type_enum": (
        "TREND_DISCOVERY", "MARKET_CONTEXT_RESEARCH", "ACTIVE_LISTING_SEARCH",
    ),
    "run_status_enum": (
        "CREATED", "MOCK_COMPLETED", "LIVE_COMPLETED",
        "PROVIDER_DISABLED", "ERROR",
    ),
    "signal_strength_enum": (
        "WATCHLIST", "DISCOVERY", "NEEDS_REVIEW", "REJECTED",
    ),
    "source_type_enum": (
        "PUBLIC_ACTIVE_LISTING", "MANUFACTURER_SPECIFICATION",
        "PUBLIC_MARKET_CONTEXT", "FIRST_PARTY_TRANSACTION",
        "LICENSED_TRANSACTION_DATA", "CLIENT_PROVIDED_SALE_RECEIPT",
        "FOUNDER_OWNED_VERIFIED_SALE", "AUTHORIZED_MERCHANT_TRANSACTION",
    ),
    "price_type_enum": (
        "ASKING_PRICE", "CONFIRMED_TRANSACTION_PRICE", "UNKNOWN", "NOT_APPLICABLE",
    ),
    "comp_eligibility_enum": (
        "NOT_A_COMP", "CANDIDATE_ONLY", "MARKET_CONTEXT_ONLY",
        "ELIGIBLE_AFTER_REVIEW",
    ),
    "comp_quality_grade_enum": ("A", "B", "C", "D", "E"),
    "transaction_status_enum": (
        "RECEIVED_PENDING_REVIEW", "CONFIRMED_WITH_EVIDENCE",
        "REJECTED_INSUFFICIENT_EVIDENCE",
    ),
    "privacy_class_enum": (
        "PRIVATE_BY_DEFAULT", "APPROVED_DERIVATIVE_ONLY", "PUBLIC_SAFE_APPROVED",
    ),
    "comp_set_intended_use_enum": (
        "MARKET_CONTEXT_RESEARCH", "AIOV_DRAFT_INPUT",
        "MARKETREADY_POSITIONING", "VALUE_SUPPORT_REVIEW",
    ),
    "comp_set_status_enum": (
        "DRAFT_RESEARCH", "NEEDS_REVIEW", "NOT_READY_FOR_VALUE_SUPPORT",
        "READY_FOR_DRAFT_ANALYSIS", "APPROVED_FOR_LIMITED_USE",
    ),
    "rights_status_enum": (
        "TERMS_REVIEW_PENDING", "INTERNAL_RESEARCH_ONLY",
        "EVAL_DERIVATIVE_ALLOWED", "TRAINING_ALLOWED",
        "PUBLIC_DISPLAY_ALLOWED", "RESTRICTED_DO_NOT_EXPORT",
    ),
    "pair_batch_type_enum": (
        "IDENTITY_NORMALIZATION", "LISTING_VS_TRANSACTION_CLASSIFICATION",
        "COMP_QUALITY_GRADING", "UNSUPPORTED_VALUE_CLAIM_DETECTION",
        "EVIDENCE_SUFFICIENCY_REVIEW", "VALUE_RANGE_WITHHOLDING",
        "MARKETREADY_CLAIM_PERMISSION",
    ),
    "pair_batch_status_enum": (
        "DRAFT_CANDIDATES", "READY_FOR_VALIDATOR", "APPROVED_FOR_EVAL",
        "APPROVED_FOR_TRAINING", "REJECTED",
    ),
    "training_pair_use_class_enum": (
        "CANDIDATE_ONLY", "EVAL_ONLY", "TRAINING_ELIGIBLE",
    ),
    "public_claim_permission_enum": (
        "PUBLIC_SAFE_APPROVED", "PUBLIC_SAFE_WITH_REQUIRED_DISCLOSURE",
        "INTERNAL_ONLY", "BLOCKED_FROM_PUBLIC_MARKETING",
    ),
    "marketready_package_status_enum": (
        "NOT_READY", "DRAFT_INPUTS_READY", "APPROVED_CLAIMS_READY",
        "EXPORT_BLOCKED",
    ),
    "artifact_type_enum": (
        "PROVIDER_RAW_RESPONSE", "NORMALIZED_OBSERVATION_BATCH",
        "NORMALIZED_TREND_SIGNAL_BATCH", "COMP_SET_RECEIPT",
        "PAIR_CANDIDATES_JSONL", "PAIR_APPROVED_EVAL_JSONL",
        "PAIR_APPROVED_TRAINING_JSONL", "DATASET_MANIFEST",
        "DATASET_SHA256SUMS", "PUBLIC_DEED_PREVIEW", "MARKETREADY_MEDIA",
    ),
    "artifact_privacy_class_enum": (
        "PRIVATE_EVIDENCE", "MARKET_OBSERVATIONS", "DERIVED_DATASETS",
        "PUBLIC_ASSETS",
    ),
}


def _enum(name: str) -> postgresql.ENUM:
    return postgresql.ENUM(*ENUMS[name], name=name, create_type=False)


def upgrade() -> None:
    bind = op.get_bind()
    for name, values in ENUMS.items():
        vlist = ", ".join(f"'{v}'" for v in values)
        bind.execute(sa.text(f"CREATE TYPE {name} AS ENUM ({vlist})"))

    # ── 15 · ArtifactRegistry (created first · others FK to it) ──────
    op.create_table(
        "artifact_registry",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("bucket", sa.String(120), nullable=False, index=True),
        sa.Column("object_key", sa.String(500), nullable=False),
        sa.Column("artifact_type", _enum("artifact_type_enum"), nullable=False),
        sa.Column("privacy_class", _enum("artifact_privacy_class_enum"), nullable=False),
        sa.Column("owner_organization_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("organizations.id", ondelete="SET NULL")),
        sa.Column("asset_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("assets.id", ondelete="SET NULL")),
        sa.Column("goods_id", postgresql.UUID(as_uuid=True)),
        sa.Column("discovery_run_id", postgresql.UUID(as_uuid=True)),
        sa.Column("pair_batch_id", postgresql.UUID(as_uuid=True)),
        sa.Column("sha256", sa.String(64), nullable=False, index=True),
        sa.Column("mime_type", sa.String(120)),
        sa.Column("byte_size", sa.Integer, nullable=False, server_default="0"),
        sa.Column("rights_status", _enum("rights_status_enum"), nullable=False,
                  server_default="INTERNAL_RESEARCH_ONLY"),
        sa.Column("retention_policy", sa.String(120)),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
    )

    # ── 1 · SourceConnector ────────────────────────────────────────
    op.create_table(
        "source_connectors",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("provider_name", _enum("provider_name_enum"), nullable=False, unique=True),
        sa.Column("connector_purpose", sa.String(255), nullable=False),
        sa.Column("provider_status", _enum("provider_status_enum"), nullable=False,
                  server_default="NOT_CONFIGURED"),
        sa.Column("live_calls_enabled", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("terms_review_status", _enum("terms_review_status_enum"), nullable=False,
                  server_default="TERMS_REVIEW_PENDING"),
        sa.Column("last_health_check_at", sa.DateTime(timezone=True)),
        sa.Column("last_error_message", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # ── 2 · DiscoveryRun ───────────────────────────────────────────
    op.create_table(
        "discovery_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("run_id", sa.String(80), unique=True, nullable=False),
        sa.Column("provider", _enum("provider_name_enum"), nullable=False),
        sa.Column("run_type", _enum("run_type_enum"), nullable=False),
        sa.Column("query", sa.Text, nullable=False),
        sa.Column("goods_class", _enum("goods_class_enum")),
        sa.Column("category", sa.String(120)),
        sa.Column("status", _enum("run_status_enum"), nullable=False, server_default="CREATED"),
        sa.Column("raw_artifact_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("artifact_registry.id", ondelete="SET NULL")),
        sa.Column("normalized_artifact_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("artifact_registry.id", ondelete="SET NULL")),
        sa.Column("raw_sha256", sa.String(64)),
        sa.Column("normalized_sha256", sa.String(64)),
        sa.Column("error_message", sa.Text),
        sa.Column("initiated_by", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # ── 3 · TrendSignal ────────────────────────────────────────────
    op.create_table(
        "trend_signals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("discovery_run_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("discovery_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("signal_name", sa.String(255), nullable=False),
        sa.Column("goods_class", _enum("goods_class_enum"), nullable=False),
        sa.Column("category", sa.String(120)),
        sa.Column("manufacturer", sa.String(120)),
        sa.Column("model", sa.String(255)),
        sa.Column("signal_strength", _enum("signal_strength_enum"), nullable=False,
                  server_default="DISCOVERY"),
        sa.Column("classification", sa.String(32), nullable=False, server_default="TREND_SIGNAL"),
        sa.Column("comp_eligibility", _enum("comp_eligibility_enum"), nullable=False,
                  server_default="NOT_A_COMP"),
        sa.Column("evidence_basis", sa.Text),
        sa.Column("recommended_market_query", sa.Text),
        sa.Column("source_limitations", postgresql.JSONB, nullable=False, server_default="[]"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # ── 4 · CanonicalGood ──────────────────────────────────────────
    op.create_table(
        "canonical_goods",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("goods_id", sa.String(120), unique=True, nullable=False),
        sa.Column("goods_class", _enum("goods_class_enum"), nullable=False),
        sa.Column("category", sa.String(120)),
        sa.Column("manufacturer", sa.String(120)),
        sa.Column("model", sa.String(255)),
        sa.Column("canonical_title", sa.String(500), nullable=False),
        sa.Column("normalized_attributes", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("identity_status", _enum("goods_identity_status_enum"), nullable=False,
                  server_default="NORMALIZED_PENDING_REVIEW"),
        sa.Column("primary_asset_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("assets.id", ondelete="SET NULL")),
        sa.Column("embedding_json", postgresql.JSONB),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # ── 5 · GoodsIdentifier ────────────────────────────────────────
    op.create_table(
        "goods_identifiers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("goods_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("canonical_goods.id", ondelete="CASCADE"), nullable=False),
        sa.Column("identifier_type", _enum("identifier_type_enum"), nullable=False),
        sa.Column("identifier_value", sa.String(255), nullable=False),
        sa.Column("source_provider", _enum("provider_name_enum")),
        sa.Column("disclosure_class", _enum("public_claim_permission_enum"), nullable=False,
                  server_default="INTERNAL_ONLY"),
        sa.Column("review_status", _enum("goods_identity_status_enum"), nullable=False,
                  server_default="NORMALIZED_PENDING_REVIEW"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # ── 6 · MarketObservation ──────────────────────────────────────
    op.create_table(
        "market_observations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("observation_id", sa.String(120), unique=True, nullable=False),
        sa.Column("goods_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("canonical_goods.id", ondelete="CASCADE"), nullable=False),
        sa.Column("discovery_run_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("discovery_runs.id", ondelete="SET NULL")),
        sa.Column("source_provider", _enum("provider_name_enum"), nullable=False),
        sa.Column("source_type", _enum("source_type_enum"), nullable=False),
        sa.Column("source_reference", sa.Text),
        sa.Column("title_raw", sa.Text),
        sa.Column("title_normalized", sa.Text),
        sa.Column("observed_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("condition_claimed", sa.String(64)),
        sa.Column("price_amount", sa.Numeric(14, 2)),
        sa.Column("price_currency", sa.String(3)),
        sa.Column("price_type", _enum("price_type_enum"), nullable=False, server_default="UNKNOWN"),
        sa.Column("transaction_confirmed", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("item_location_summary", sa.String(255)),
        sa.Column("listing_status", sa.String(64)),
        sa.Column("image_reference_policy", sa.String(64)),
        sa.Column("identity_match_score", sa.Float),
        sa.Column("comp_eligibility", _enum("comp_eligibility_enum"), nullable=False,
                  server_default="CANDIDATE_ONLY"),
        sa.Column("comp_quality_grade", _enum("comp_quality_grade_enum")),
        sa.Column("limitations", postgresql.JSONB, nullable=False, server_default="[]"),
        sa.Column("rights_status", _enum("rights_status_enum"), nullable=False,
                  server_default="INTERNAL_RESEARCH_ONLY"),
        sa.Column("raw_artifact_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("artifact_registry.id", ondelete="SET NULL")),
        sa.Column("normalized_sha256", sa.String(64)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # ── 7 · TransactionEvidence ────────────────────────────────────
    op.create_table(
        "transaction_evidences",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("transaction_id", sa.String(120), unique=True, nullable=False),
        sa.Column("goods_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("canonical_goods.id", ondelete="CASCADE"), nullable=False),
        sa.Column("asset_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("assets.id", ondelete="SET NULL")),
        sa.Column("source_type", _enum("source_type_enum"), nullable=False),
        sa.Column("transaction_status", _enum("transaction_status_enum"), nullable=False,
                  server_default="RECEIVED_PENDING_REVIEW"),
        sa.Column("sale_price_amount", sa.Numeric(14, 2)),
        sa.Column("sale_price_currency", sa.String(3)),
        sa.Column("transaction_date", sa.DateTime(timezone=True)),
        sa.Column("evidence_manifest_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("evidence_manifests.id", ondelete="SET NULL")),
        sa.Column("privacy_class", _enum("privacy_class_enum"), nullable=False,
                  server_default="PRIVATE_BY_DEFAULT"),
        sa.Column("rights_status", _enum("rights_status_enum"), nullable=False,
                  server_default="TERMS_REVIEW_PENDING"),
        sa.Column("training_permission", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("validator_receipt_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("validator_reviews.id", ondelete="SET NULL")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # ── 8 · CompSet ────────────────────────────────────────────────
    op.create_table(
        "comp_sets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("comp_set_id", sa.String(120), unique=True, nullable=False),
        sa.Column("goods_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("canonical_goods.id", ondelete="CASCADE"), nullable=False),
        sa.Column("asset_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("assets.id", ondelete="SET NULL")),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("intended_use", _enum("comp_set_intended_use_enum"), nullable=False,
                  server_default="MARKET_CONTEXT_RESEARCH"),
        sa.Column("comp_set_status", _enum("comp_set_status_enum"), nullable=False,
                  server_default="DRAFT_RESEARCH"),
        sa.Column("grade_summary", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("limitations", postgresql.JSONB, nullable=False, server_default="[]"),
        sa.Column("confirmed_transaction_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("active_listing_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("trend_signal_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("validator_status", sa.String(64)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # ── 9 · CompSetMember ──────────────────────────────────────────
    op.create_table(
        "comp_set_members",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("comp_set_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("comp_sets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("observation_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("market_observations.id", ondelete="CASCADE")),
        sa.Column("transaction_evidence_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("transaction_evidences.id", ondelete="CASCADE")),
        sa.Column("trend_signal_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("trend_signals.id", ondelete="CASCADE")),
        sa.Column("quality_grade", _enum("comp_quality_grade_enum"), nullable=False),
        sa.Column("inclusion_reason", sa.Text),
        sa.Column("limitations", postgresql.JSONB, nullable=False, server_default="[]"),
        sa.Column("included_by", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # ── 10 · SourceRightsRecord ────────────────────────────────────
    op.create_table(
        "source_rights_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("source_connector_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("source_connectors.id", ondelete="SET NULL")),
        sa.Column("artifact_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("artifact_registry.id", ondelete="SET NULL")),
        sa.Column("data_class", sa.String(64), nullable=False),
        sa.Column("acquisition_method", sa.String(64), nullable=False),
        sa.Column("rights_status", _enum("rights_status_enum"), nullable=False,
                  server_default="INTERNAL_RESEARCH_ONLY"),
        sa.Column("training_eligible", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("public_display_eligible", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("retention_policy", sa.String(120)),
        sa.Column("review_notes", sa.Text),
        sa.Column("reviewed_by", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("reviewed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # ── 11 · PairBatch ─────────────────────────────────────────────
    op.create_table(
        "pair_batches",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("batch_id", sa.String(120), unique=True, nullable=False),
        sa.Column("goods_class", _enum("goods_class_enum"), nullable=False),
        sa.Column("batch_type", _enum("pair_batch_type_enum"), nullable=False),
        sa.Column("batch_status", _enum("pair_batch_status_enum"), nullable=False,
                  server_default="DRAFT_CANDIDATES"),
        sa.Column("source_rights_status", _enum("rights_status_enum"), nullable=False,
                  server_default="INTERNAL_RESEARCH_ONLY"),
        sa.Column("validator_status", sa.String(64)),
        sa.Column("training_eligible", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("manifest_artifact_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("artifact_registry.id", ondelete="SET NULL")),
        sa.Column("manifest_sha256", sa.String(64)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # ── 12 · TrainingPair ──────────────────────────────────────────
    op.create_table(
        "training_pairs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("pair_id", sa.String(120), unique=True, nullable=False),
        sa.Column("pair_batch_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("pair_batches.id", ondelete="CASCADE"), nullable=False),
        sa.Column("goods_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("canonical_goods.id", ondelete="SET NULL")),
        sa.Column("pair_type", _enum("pair_batch_type_enum"), nullable=False),
        sa.Column("source_lineage", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("input_json", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("expected_output_json", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("validator_status", sa.String(64), nullable=False,
                  server_default="VALIDATOR_REVIEW_REQUIRED"),
        sa.Column("source_rights_status", _enum("rights_status_enum"), nullable=False,
                  server_default="INTERNAL_RESEARCH_ONLY"),
        sa.Column("use_class", _enum("training_pair_use_class_enum"), nullable=False,
                  server_default="CANDIDATE_ONLY"),
        sa.Column("training_eligible", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("artifact_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("artifact_registry.id", ondelete="SET NULL")),
        sa.Column("sha256", sa.String(64)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # ── 13 · ApprovedClaim ─────────────────────────────────────────
    op.create_table(
        "approved_claims",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("asset_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("assets.id", ondelete="CASCADE")),
        sa.Column("goods_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("canonical_goods.id", ondelete="SET NULL")),
        sa.Column("claim_text", sa.Text, nullable=False),
        sa.Column("claim_type", sa.String(64), nullable=False),
        sa.Column("source_lineage", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("validator_status", sa.String(64)),
        sa.Column("public_permission", _enum("public_claim_permission_enum"), nullable=False,
                  server_default="INTERNAL_ONLY"),
        sa.Column("required_disclosure", sa.Text),
        sa.Column("applicable_surfaces", postgresql.JSONB, nullable=False, server_default="[]"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # ── 14 · MarketReadyDataLink ───────────────────────────────────
    op.create_table(
        "marketready_data_links",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("asset_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("assets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("goods_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("canonical_goods.id", ondelete="CASCADE"), nullable=False),
        sa.Column("comp_set_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("comp_sets.id", ondelete="SET NULL")),
        sa.Column("approved_claim_ids", postgresql.JSONB, nullable=False, server_default="[]"),
        sa.Column("package_status", _enum("marketready_package_status_enum"), nullable=False,
                  server_default="NOT_READY"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    for table in [
        "marketready_data_links",
        "approved_claims",
        "training_pairs",
        "pair_batches",
        "source_rights_records",
        "comp_set_members",
        "comp_sets",
        "transaction_evidences",
        "market_observations",
        "goods_identifiers",
        "canonical_goods",
        "trend_signals",
        "discovery_runs",
        "source_connectors",
        "artifact_registry",
    ]:
        op.drop_table(table)
    for enum_name in list(ENUMS.keys()):
        op.execute(f"DROP TYPE IF EXISTS {enum_name}")
