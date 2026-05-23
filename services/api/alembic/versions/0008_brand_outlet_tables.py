"""brand outlet tables · 2 tables

Revision ID: 0008_brand_outlet_tables
Revises: 0007_brand_outlet_enum_additions
Create Date: 2026-05-22

brand_watchlists + brand_placement_signals · runs after 0007 commits.
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0008_brand_outlet_tables"
down_revision = "0007_brand_outlet_enum_additions"
branch_labels = None
depends_on = None


def _enum(name: str) -> postgresql.ENUM:
    return postgresql.ENUM(name=name, create_type=False)


def upgrade() -> None:
    # brand_watchlists
    op.create_table(
        "brand_watchlists",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("brand_slug", sa.String(120), unique=True, nullable=False),
        sa.Column("brand_name", sa.String(255), nullable=False),
        sa.Column("merchandising_lane", _enum("merchandising_lane_enum"), nullable=False,
                  server_default="OTHER"),
        sa.Column("priority_tier", _enum("brand_priority_tier_enum"), nullable=False,
                  server_default="B"),
        sa.Column("sourcing_status", _enum("brand_sourcing_status_enum"), nullable=False,
                  server_default="NOT_REVIEWED"),
        sa.Column("policy_risk_flag", _enum("policy_risk_flag_enum"), nullable=False,
                  server_default="NONE"),
        sa.Column("notes", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # brand_placement_signals
    op.create_table(
        "brand_placement_signals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("brand_watchlist_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("brand_watchlists.id", ondelete="CASCADE"),
                  nullable=False, index=True),
        sa.Column("opportunity_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("product_opportunities.id", ondelete="SET NULL"), index=True),
        sa.Column("source_provider", sa.String(64), nullable=False, server_default="EBAY_BRAND_OUTLET"),
        sa.Column("marketplace", sa.String(32), nullable=False, server_default="EBAY_US"),
        sa.Column("merchandising_lane", _enum("merchandising_lane_enum"), nullable=False,
                  server_default="OTHER"),
        sa.Column("promotional_language", sa.Text),
        sa.Column("signal_status", sa.String(64), nullable=False,
                  server_default="MERCHANDISED_BRAND_WATCHLIST"),
        # Doctrine pins · application layer refuses to flip these.
        sa.Column("sales_confirmed", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("supplier_authorization_confirmed", sa.Boolean, nullable=False,
                  server_default=sa.text("false")),
        sa.Column("rights_status", sa.String(64), nullable=False,
                  server_default="INTERNAL_RESEARCH_ONLY"),
        sa.Column("training_eligible", sa.Boolean, nullable=False, server_default=sa.text("false")),
        # signal_class · uses existing SEARCH_DEMAND_SIGNAL value as the
        # SQL server-default (existing pre-0007 value) to avoid the
        # session-cache rule · Python model default still applies the
        # canonical BRANDED_COMMERCE_PLACEMENT at INSERT time.
        sa.Column("signal_class", _enum("signal_class_enum"), nullable=False,
                  server_default="SEARCH_DEMAND_SIGNAL"),
        sa.Column("recommended_next_steps_json", postgresql.JSONB, nullable=False, server_default="[]"),
        sa.Column("raw_artifact_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("artifact_registry.id", ondelete="SET NULL")),
        sa.Column("captured_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    for table in ["brand_placement_signals", "brand_watchlists"]:
        op.drop_table(table)
