"""itad partner feed tables · runs after enum additions commit

Revision ID: 0004_itad_tables
Revises: 0003_itad_enum_additions
Create Date: 2026-05-22

Creates the 3 ITAD tables. Safe to use the new enum values added in
0003 because that migration committed before this one runs.
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0004_itad_tables"
down_revision = "0003_itad_enum_additions"
branch_labels = None
depends_on = None


def _enum(name: str) -> postgresql.ENUM:
    return postgresql.ENUM(name=name, create_type=False)


def upgrade() -> None:
    # itad_partners
    op.create_table(
        "itad_partners",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("slug", sa.String(80), unique=True, nullable=False),
        sa.Column("company_name", sa.String(255), nullable=False),
        sa.Column("company_url", sa.String(500)),
        sa.Column("partnership_status", _enum("itad_partnership_status_enum"), nullable=False,
                  server_default="RESEARCH_VERIFIED"),
        sa.Column("compute_coverage_summary", sa.Text),
        sa.Column("feed_format", _enum("itad_feed_format_enum"), nullable=False,
                  server_default="UNKNOWN"),
        sa.Column("agreement_status", _enum("itad_agreement_status_enum"), nullable=False,
                  server_default="NONE"),
        # NB: server_default uses an existing enum value (TERMS_REVIEW_PENDING) ·
        # PostgreSQL refuses to bake a newly-added enum value into a table DDL
        # until the session that added it has been recycled. The application
        # layer (ItadPartner model) still sets rights_scope=AGREEMENT_REQUIRED
        # at INSERT time, so functional behavior is unchanged.
        sa.Column("rights_scope", _enum("rights_status_enum"), nullable=False,
                  server_default="TERMS_REVIEW_PENDING"),
        sa.Column("contact_status", _enum("itad_contact_status_enum"), nullable=False,
                  server_default="NOT_CONTACTED"),
        sa.Column("contact_notes", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
    )

    # itad_feed_import_runs
    op.create_table(
        "itad_feed_import_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("partner_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("itad_partners.id", ondelete="CASCADE"),
                  nullable=False, index=True),
        sa.Column("received_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
        sa.Column("raw_artifact_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("artifact_registry.id", ondelete="SET NULL")),
        sa.Column("manifest_sha256", sa.String(64)),
        sa.Column("record_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("import_status", _enum("itad_feed_import_status_enum"), nullable=False,
                  server_default="PENDING"),
        sa.Column("validator_status", sa.String(64)),
        sa.Column("error_message", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
    )

    # partner_transaction_observations
    op.create_table(
        "partner_transaction_observations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("partner_transaction_ref", sa.String(120), unique=True, nullable=False),
        sa.Column("partner_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("itad_partners.id", ondelete="CASCADE"),
                  nullable=False, index=True),
        sa.Column("feed_import_run_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("itad_feed_import_runs.id", ondelete="SET NULL")),
        sa.Column("goods_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("canonical_goods.id", ondelete="CASCADE"),
                  nullable=False, index=True),
        sa.Column("asset_type", _enum("itad_asset_type_enum"), nullable=False,
                  server_default="GPU"),
        sa.Column("manufacturer", sa.String(120)),
        sa.Column("model", sa.String(255)),
        sa.Column("form_factor", _enum("itad_form_factor_enum"), nullable=False,
                  server_default="UNKNOWN"),
        sa.Column("memory_configuration", sa.String(120)),
        sa.Column("quantity", sa.Integer, nullable=False, server_default="1"),
        sa.Column("condition_class", _enum("itad_condition_class_enum"), nullable=False,
                  server_default="UNKNOWN"),
        sa.Column("test_status", sa.String(120)),
        sa.Column("system_configuration_summary", sa.Text),
        sa.Column("transaction_type", _enum("itad_transaction_type_enum"), nullable=False,
                  server_default="UNKNOWN"),
        sa.Column("transaction_date", sa.DateTime(timezone=True)),
        sa.Column("amount_usd", sa.Numeric(14, 2)),
        sa.Column("amount_band", sa.String(120)),
        sa.Column("amount_disclosure_type", _enum("itad_amount_disclosure_type_enum"),
                  nullable=False, server_default="REDACTED"),
        sa.Column("geography_region", sa.String(120)),
        sa.Column("configuration_match_score", sa.Float),
        sa.Column("rights_status", _enum("rights_status_enum"), nullable=False,
                  server_default="TERMS_REVIEW_PENDING"),
        sa.Column("comp_quality_grade", _enum("comp_quality_grade_enum")),
        sa.Column("training_eligible", sa.Boolean, nullable=False,
                  server_default=sa.text("false")),
        sa.Column("public_display_eligible", sa.Boolean, nullable=False,
                  server_default=sa.text("false")),
        sa.Column("raw_artifact_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("artifact_registry.id", ondelete="SET NULL")),
        sa.Column("normalized_sha256", sa.String(64)),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    for table in [
        "partner_transaction_observations",
        "itad_feed_import_runs",
        "itad_partners",
    ]:
        op.drop_table(table)
