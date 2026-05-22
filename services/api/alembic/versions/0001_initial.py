"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-05-22

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


# ── enums (created once, referenced everywhere) ─────────────────────────────
def _enum(name: str, *values: str) -> sa.Enum:
    return sa.Enum(*values, name=name, native_enum=True, create_type=False)


def upgrade() -> None:
    bind = op.get_bind()

    enums = {
        "org_role_enum": ("PLATFORM_ADMIN", "ORG_ADMIN", "ORG_ANALYST", "ORG_VIEWER"),
        "ens_status_enum": (
            "UNRESERVED", "RESERVED_NOT_ISSUED", "ISSUED_OFFCHAIN", "ISSUED_ONCHAIN", "REVOKED",
        ),
        "asset_class_enum": (
            "COMPUTE_HARDWARE", "REAL_ESTATE", "EQUIPMENT", "LUXURY_GOODS",
            "DATASET", "AI_ASSET", "OTHER",
        ),
        "asset_status_enum": (
            "DRAFT", "EVIDENCE_INTAKE", "RESEARCH_IN_PROGRESS", "AIOV_DRAFTED",
            "VALIDATOR_IN_REVIEW", "PASSED_FOR_PACKAGING", "DEED_DRAFTED",
            "PUBLIC_VERIFICATION_PUBLISHED", "ARCHIVED",
        ),
        "condition_status_enum": ("NEW", "USED", "REFURBISHED", "UNKNOWN"),
        "intended_use_enum": (
            "INFERENCE", "TRAINING", "RENDERING", "RENTAL_COMPUTE",
            "EDGE_INFERENCE", "GENERAL_AI_WORKLOAD",
        ),
        "evidence_type_enum": (
            "PURCHASE_RECEIPT", "PRODUCT_SPECIFICATION", "SERIAL_OR_PHOTO",
            "NVIDIA_SMI_CAPTURE", "BENCHMARK_OUTPUT", "THERMAL_POWER_OUTPUT",
            "SYSTEM_SPECIFICATION", "MAINTENANCE_RECORD", "PRIOR_LISTING", "OTHER",
        ),
        "visibility_enum": ("PRIVATE", "PUBLIC_APPROVED"),
        "ingestion_status_enum": (
            "UPLOADED", "HASHING", "INDEXING", "INDEXED", "EXTRACTION_FAILED",
        ),
        "manifest_status_enum": ("CURRENT", "SUPERSEDED"),
        "source_lane_enum": (
            "PRIVATE_EVIDENCE", "PUBLIC_WEB", "INTERNAL_COMPARABLES", "MIXED",
        ),
        "research_status_enum": ("PENDING", "COMPLETED", "FAILED"),
        "evidence_classification_enum": (
            "MANUFACTURER_SPEC", "LISTING_PRICE", "CONFIRMED_SALE_PRICE",
            "AUCTION_RESULT", "BENCHMARK_REFERENCE", "MARKET_COMMENTARY", "UNKNOWN",
        ),
        "workflow_type_enum": (
            "EVIDENCE_SUMMARY", "RESEARCH_SYNTHESIS", "AIOV_DRAFT",
            "VALIDATOR_ASSIST", "PUBLIC_DEED_SUMMARY", "EDGE_EVIDENCE_CLASSIFICATION",
        ),
        "ai_output_status_enum": ("GENERATED", "FAILED", "NOT_CONFIGURED"),
        "aiov_status_enum": ("DRAFT", "GENERATED_FOR_VALIDATOR_REVIEW", "SUPERSEDED"),
        "validator_status_enum": (
            "NOT_STARTED", "IN_REVIEW", "FAILED_REQUIRES_REPAIR",
            "PASSED_FOR_PACKAGING", "APPROVED_FOR_PUBLIC_VERIFICATION",
        ),
        "deed_status_enum": (
            "DRAFT_REVIEW_RECORD", "PASSED_FOR_PACKAGING",
            "APPROVED_FOR_PUBLIC", "SUPERSEDED", "REVOKED",
        ),
        "identity_type_enum": ("ORGANIZATION", "ASSET", "DEED", "EDGE_NODE"),
        "issuance_mode_enum": ("RESERVED", "MOCK", "OFFCHAIN_CCIP", "ONCHAIN_WRAPPED"),
        "identity_status_enum": ("RESERVED_NOT_ISSUED", "ISSUED", "REVOKED"),
        "enrollment_status_enum": ("PENDING", "ENROLLED", "ENROLLED_DEMO", "STALE", "REVOKED"),
    }
    for name, values in enums.items():
        sa.Enum(*values, name=name, native_enum=True).create(bind, checkfirst=True)

    # ── users ──
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("name", sa.String(255)),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("is_platform_admin", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # ── organizations ──
    op.create_table(
        "organizations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(64), nullable=False, unique=True),
        sa.Column("ens_label", sa.String(64), unique=True),
        sa.Column("ens_name", sa.String(255)),
        sa.Column("ens_status", _enum("ens_status_enum"), nullable=False, server_default="UNRESERVED"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_organizations_ens_label", "organizations", ["ens_label"])

    # ── memberships ──
    op.create_table(
        "organization_memberships",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", _enum("org_role_enum"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("organization_id", "user_id", name="uq_membership_org_user"),
    )

    # ── assets ──
    op.create_table(
        "assets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("public_asset_reference", sa.String(64), nullable=False),
        sa.Column("asset_class", _enum("asset_class_enum"), nullable=False),
        sa.Column("category", sa.String(64)),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("status", _enum("asset_status_enum"), nullable=False, server_default="DRAFT"),
        sa.Column("private_serial_number", sa.String(255)),
        sa.Column("client_internal_reference", sa.String(255)),
        sa.Column("created_by", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("organization_id", "public_asset_reference", name="uq_asset_org_public_ref"),
    )
    op.create_index("ix_assets_organization_id", "assets", ["organization_id"])

    op.create_table(
        "compute_asset_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("asset_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("assets.id", ondelete="CASCADE"), unique=True, nullable=False),
        sa.Column("manufacturer", sa.String(128)),
        sa.Column("model", sa.String(255)),
        sa.Column("gpu_count", sa.Integer),
        sa.Column("vram_per_gpu_gb", sa.Integer),
        sa.Column("cpu", sa.String(255)),
        sa.Column("ram_gb", sa.Integer),
        sa.Column("storage_description", sa.Text),
        sa.Column("networking_description", sa.Text),
        sa.Column("operating_system", sa.String(128)),
        sa.Column("condition_status", _enum("condition_status_enum")),
        sa.Column("operational_status", sa.String(128)),
        sa.Column("intended_use", _enum("intended_use_enum")),
        sa.Column("purchase_date", sa.Date),
        sa.Column("purchase_cost_private", sa.Numeric(14, 2)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # ── edge_nodes ── (declared early · referenced by evidence + ens)
    op.create_table(
        "edge_nodes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("node_name", sa.String(128), nullable=False),
        sa.Column("node_slug", sa.String(64), nullable=False),
        sa.Column("ens_identity_id", postgresql.UUID(as_uuid=True)),
        sa.Column("enrollment_status", _enum("enrollment_status_enum"),
                  nullable=False, server_default="PENDING"),
        sa.Column("last_heartbeat_at", sa.DateTime(timezone=True)),
        sa.Column("software_version", sa.String(64)),
        sa.Column("hardware_summary_json", postgresql.JSONB),
        sa.Column("public_key_or_device_fingerprint", sa.String(512)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_edge_nodes_organization_id", "edge_nodes", ["organization_id"])

    # ── evidence_items ──
    op.create_table(
        "evidence_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("asset_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("assets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("filename", sa.String(512), nullable=False),
        sa.Column("storage_key", sa.String(1024), nullable=False),
        sa.Column("content_type", sa.String(128)),
        sa.Column("byte_size", sa.Integer, nullable=False, server_default="0"),
        sa.Column("evidence_type", _enum("evidence_type_enum"), nullable=False),
        sa.Column("visibility", _enum("visibility_enum"), nullable=False, server_default="PRIVATE"),
        sa.Column("ingestion_status", _enum("ingestion_status_enum"),
                  nullable=False, server_default="UPLOADED"),
        sa.Column("sha256_hash", sa.String(64)),
        sa.Column("uploaded_by", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("provenance", sa.String(64)),
        sa.Column("edge_node_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("edge_nodes.id", ondelete="SET NULL")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_evidence_items_asset_id", "evidence_items", ["asset_id"])
    op.create_index("ix_evidence_items_organization_id", "evidence_items", ["organization_id"])
    op.create_index("ix_evidence_items_sha256_hash", "evidence_items", ["sha256_hash"])

    op.create_table(
        "evidence_manifests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("asset_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("assets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("version", sa.Integer, nullable=False, server_default="1"),
        sa.Column("manifest_json", postgresql.JSONB, nullable=False),
        sa.Column("manifest_sha256", sa.String(64), nullable=False),
        sa.Column("status", _enum("manifest_status_enum"),
                  nullable=False, server_default="CURRENT"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_evidence_manifests_asset_id", "evidence_manifests", ["asset_id"])
    op.create_index("ix_evidence_manifests_sha", "evidence_manifests", ["manifest_sha256"])

    op.create_table(
        "extracted_documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("evidence_item_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("evidence_items.id", ondelete="CASCADE"), unique=True, nullable=False),
        sa.Column("extraction_status", sa.String(32), nullable=False, server_default="PENDING"),
        sa.Column("extracted_text_private", sa.Text),
        sa.Column("chunk_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("metadata_json", postgresql.JSONB),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "evidence_chunks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("evidence_item_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("evidence_items.id", ondelete="CASCADE"), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("asset_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("assets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("chunk_index", sa.Integer, nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("citation_locator", sa.String(255)),
        sa.Column("metadata_json", postgresql.JSONB),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_evidence_chunks_asset_id", "evidence_chunks", ["asset_id"])
    op.create_index("ix_evidence_chunks_evidence_item_id", "evidence_chunks", ["evidence_item_id"])

    # ── research ──
    op.create_table(
        "research_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("asset_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("assets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("initiated_by", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("query", sa.Text, nullable=False),
        sa.Column("source_lane", _enum("source_lane_enum"), nullable=False),
        sa.Column("provider", sa.String(64)),
        sa.Column("model_used", sa.String(128)),
        sa.Column("status", _enum("research_status_enum"),
                  nullable=False, server_default="PENDING"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_research_sessions_asset_id", "research_sessions", ["asset_id"])

    op.create_table(
        "research_sources",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("research_session_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("research_sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_type", sa.String(32), nullable=False),
        sa.Column("title", sa.String(512)),
        sa.Column("source_url", sa.String(2048)),
        sa.Column("publisher_domain", sa.String(255)),
        sa.Column("retrieved_at", sa.DateTime(timezone=True)),
        sa.Column("evidence_classification", _enum("evidence_classification_enum"),
                  nullable=False, server_default="UNKNOWN"),
        sa.Column("content_excerpt", sa.Text),
        sa.Column("source_hash", sa.String(64)),
        sa.Column("validator_status", sa.String(32)),
        sa.Column("extra_metadata", postgresql.JSONB),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_research_sources_session_id", "research_sources", ["research_session_id"])

    # ── ai ──
    op.create_table(
        "ai_outputs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("asset_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("assets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("workflow_type", _enum("workflow_type_enum"), nullable=False),
        sa.Column("model_provider", sa.String(64), nullable=False),
        sa.Column("model_name", sa.String(128), nullable=False),
        sa.Column("prompt_version", sa.String(64), nullable=False),
        sa.Column("input_reference_json", postgresql.JSONB, nullable=False),
        sa.Column("output_text", sa.Text),
        sa.Column("output_json", postgresql.JSONB),
        sa.Column("output_sha256", sa.String(64)),
        sa.Column("status", _enum("ai_output_status_enum"),
                  nullable=False, server_default="GENERATED"),
        sa.Column("thinking_enabled", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("error_message", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_ai_outputs_asset_id", "ai_outputs", ["asset_id"])

    op.create_table(
        "aiov_analyses",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("asset_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("assets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("version", sa.Integer, nullable=False, server_default="1"),
        sa.Column("status", _enum("aiov_status_enum"), nullable=False, server_default="DRAFT"),
        sa.Column("analysis_json", postgresql.JSONB, nullable=False),
        sa.Column("narrative", sa.Text),
        sa.Column("supporting_source_ids", postgresql.JSONB),
        sa.Column("missing_evidence_json", postgresql.JSONB),
        sa.Column("generated_by_output_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("ai_outputs.id", ondelete="SET NULL")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_aiov_analyses_asset_id", "aiov_analyses", ["asset_id"])

    # ── validator ──
    op.create_table(
        "validator_reviews",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("asset_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("assets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("aiov_analysis_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("aiov_analyses.id", ondelete="SET NULL")),
        sa.Column("version", sa.Integer, nullable=False, server_default="1"),
        sa.Column("status", _enum("validator_status_enum"),
                  nullable=False, server_default="NOT_STARTED"),
        sa.Column("protocol", sa.String(64), nullable=False, server_default="VALIDATE_THE_VALIDATOR"),
        sa.Column("findings_json", postgresql.JSONB),
        sa.Column("checks_json", postgresql.JSONB, nullable=False),
        sa.Column("receipt_sha256", sa.String(64), nullable=False),
        sa.Column("reviewed_by", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_validator_reviews_asset_id", "validator_reviews", ["asset_id"])
    op.create_index("ix_validator_reviews_receipt", "validator_reviews", ["receipt_sha256"])

    # ── deeds ──
    op.create_table(
        "defendable_deeds",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("asset_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("assets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("deed_reference", sa.String(128), nullable=False),
        sa.Column("version", sa.Integer, nullable=False, server_default="1"),
        sa.Column("status", _enum("deed_status_enum"),
                  nullable=False, server_default="DRAFT_REVIEW_RECORD"),
        sa.Column("deed_json", postgresql.JSONB, nullable=False),
        sa.Column("record_hash", sa.String(64), nullable=False),
        sa.Column("public_slug", sa.String(128), unique=True),
        sa.Column("is_public", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("issued_by", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("asset_id", "version", name="uq_deed_asset_version"),
    )
    op.create_index("ix_defendable_deeds_asset_id", "defendable_deeds", ["asset_id"])
    op.create_index("ix_defendable_deeds_record_hash", "defendable_deeds", ["record_hash"])

    # ── ens identities ──
    op.create_table(
        "ens_identities",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("asset_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("assets.id", ondelete="SET NULL")),
        sa.Column("deed_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("defendable_deeds.id", ondelete="SET NULL")),
        sa.Column("edge_node_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("edge_nodes.id", ondelete="SET NULL")),
        sa.Column("ens_name", sa.String(255), nullable=False, unique=True),
        sa.Column("label", sa.String(128), nullable=False),
        sa.Column("parent_name", sa.String(255), nullable=False),
        sa.Column("identity_type", _enum("identity_type_enum"), nullable=False),
        sa.Column("issuance_mode", _enum("issuance_mode_enum"),
                  nullable=False, server_default="MOCK"),
        sa.Column("status", _enum("identity_status_enum"),
                  nullable=False, server_default="RESERVED_NOT_ISSUED"),
        sa.Column("public_metadata_json", postgresql.JSONB),
        sa.Column("transaction_hash", sa.String(128)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # ── edge upload events + enrollment tokens ──
    op.create_table(
        "edge_upload_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("edge_node_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("edge_nodes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("asset_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("assets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("evidence_item_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("evidence_items.id", ondelete="SET NULL")),
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column("payload_hash", sa.String(64)),
        sa.Column("claimed_hash", sa.String(64)),
        sa.Column("verified_hash", sa.String(64)),
        sa.Column("hash_match", sa.Boolean),
        sa.Column("sync_status", sa.String(32), nullable=False, server_default="ACCEPTED"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_edge_upload_events_node_id", "edge_upload_events", ["edge_node_id"])

    op.create_table(
        "edge_enrollment_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.String(128), nullable=False, unique=True),
        sa.Column("node_name_hint", sa.String(128)),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True)),
        sa.Column("consumed_by_node_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("edge_nodes.id", ondelete="SET NULL")),
        sa.Column("created_by", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_edge_enrollment_tokens_org", "edge_enrollment_tokens", ["organization_id"])

    # ── audit ──
    op.create_table(
        "audit_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("organizations.id", ondelete="SET NULL")),
        sa.Column("actor_type", sa.String(32), nullable=False),
        sa.Column("actor_id", sa.String(128)),
        sa.Column("action", sa.String(128), nullable=False),
        sa.Column("entity_type", sa.String(64), nullable=False),
        sa.Column("entity_id", sa.String(128), nullable=False),
        sa.Column("extra_metadata", postgresql.JSONB),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_audit_events_org_id", "audit_events", ["organization_id"])


def downgrade() -> None:
    # MVP migration is a single create-all · downgrade tears the whole schema down.
    for table in [
        "audit_events",
        "edge_enrollment_tokens",
        "edge_upload_events",
        "ens_identities",
        "defendable_deeds",
        "validator_reviews",
        "aiov_analyses",
        "ai_outputs",
        "research_sources",
        "research_sessions",
        "evidence_chunks",
        "extracted_documents",
        "evidence_manifests",
        "evidence_items",
        "edge_nodes",
        "compute_asset_profiles",
        "assets",
        "organization_memberships",
        "organizations",
        "users",
    ]:
        op.drop_table(table)
    for enum_name in [
        "enrollment_status_enum", "identity_status_enum", "issuance_mode_enum",
        "identity_type_enum", "deed_status_enum", "validator_status_enum",
        "aiov_status_enum", "ai_output_status_enum", "workflow_type_enum",
        "evidence_classification_enum", "research_status_enum", "source_lane_enum",
        "manifest_status_enum", "ingestion_status_enum", "visibility_enum",
        "evidence_type_enum", "intended_use_enum", "condition_status_enum",
        "asset_status_enum", "asset_class_enum", "ens_status_enum", "org_role_enum",
    ]:
        op.execute(f"DROP TYPE IF EXISTS {enum_name}")
