"""Admin · operator summary read endpoint.

A single rollup JSON for the founder's morning glance. Aggregates
counts that already exist across the goods + ITAD + ProductRadar
tables plus the deeds catalog. No new doctrine · no new tables ·
purely a read-only convenience view.

Mounts at `/api/v1/admin/operator-summary` (not under /goods because
this is the cross-cutting summary). Behind require_platform_admin.
"""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_platform_admin
from app.models.deed import DefendableDeed
from app.models.goods import (
    CanonicalGood,
    ItadPartner,
    SourceConnector,
)
from app.models.productradar import BrandWatchlist
from app.services.connector_registry import CONNECTOR_DEFINITIONS, resolve_status


router = APIRouter(prefix="/admin")


@router.get("/operator-summary")
def operator_summary(
    db: Session = Depends(get_db),
    _admin=Depends(require_platform_admin),
) -> dict:
    """One-shot rollup for the founder's morning glance.

    Returns:
      · canonical_goods             total + by goods_class
      · itad_partners               total + by partnership_status
      · brand_watchlist             total + by priority_tier + by sourcing_status
      · connectors                  total + by status (live-derived)
      · public_deeds                total + by asset_class
      · latest_migration            alembic head
      · generated_at                ISO-8601 timestamp
    """
    # ── canonical goods ──────────────────────────────────────────────
    canonical_goods_total = db.query(CanonicalGood).count()
    canonical_goods_by_class_simple: dict[str, int] = {}
    for row in db.query(CanonicalGood.goods_class).all():
        key = row[0].value
        canonical_goods_by_class_simple[key] = canonical_goods_by_class_simple.get(key, 0) + 1

    # ── ITAD partners ────────────────────────────────────────────────
    itad_partners_total = db.query(ItadPartner).count()
    itad_partners_by_status: dict[str, int] = {}
    for row in db.query(ItadPartner.partnership_status).all():
        key = row[0].value
        itad_partners_by_status[key] = itad_partners_by_status.get(key, 0) + 1

    # ── brand watchlist ──────────────────────────────────────────────
    brand_watchlist_total = db.query(BrandWatchlist).count()
    brand_by_priority: dict[str, int] = {}
    brand_by_sourcing: dict[str, int] = {}
    for row in db.query(BrandWatchlist.priority_tier, BrandWatchlist.sourcing_status).all():
        pri = row[0].value
        src = row[1].value
        brand_by_priority[pri] = brand_by_priority.get(pri, 0) + 1
        brand_by_sourcing[src] = brand_by_sourcing.get(src, 0) + 1

    # ── connectors · status is live-derived (not cached) ────────────
    connectors_total = len(CONNECTOR_DEFINITIONS)
    connectors_by_status: dict[str, int] = {}
    for d in CONNECTOR_DEFINITIONS:
        status = resolve_status(d["provider_name"]).value
        connectors_by_status[status] = connectors_by_status.get(status, 0) + 1
    # Also include what's been written to the source_connectors table
    # (may diverge from live status because the table is a snapshot).
    connectors_in_db = db.query(SourceConnector).count()

    # ── public deeds ─────────────────────────────────────────────────
    public_deeds_total = (
        db.query(DefendableDeed).filter(DefendableDeed.is_public == True).count()  # noqa: E712
    )
    public_deeds_by_class_rows = (
        db.execute(text("""
            SELECT a.asset_class::text, COUNT(*)
            FROM defendable_deeds d
            JOIN assets a ON a.id = d.asset_id
            WHERE d.is_public = true
            GROUP BY a.asset_class
        """)).fetchall()
    )
    public_deeds_by_class = {row[0]: row[1] for row in public_deeds_by_class_rows}

    # ── latest migration ─────────────────────────────────────────────
    latest_migration_row = db.execute(
        text("SELECT version_num FROM alembic_version LIMIT 1")
    ).fetchone()
    latest_migration = latest_migration_row[0] if latest_migration_row else None

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "latest_migration": latest_migration,
        "canonical_goods": {
            "total": canonical_goods_total,
            "by_goods_class": canonical_goods_by_class_simple,
        },
        "itad_partners": {
            "total": itad_partners_total,
            "by_partnership_status": itad_partners_by_status,
        },
        "brand_watchlist": {
            "total": brand_watchlist_total,
            "by_priority_tier": brand_by_priority,
            "by_sourcing_status": brand_by_sourcing,
        },
        "connectors": {
            "total_definitions": connectors_total,
            "rows_in_db": connectors_in_db,
            "by_live_status": connectors_by_status,
        },
        "public_deeds": {
            "total": public_deeds_total,
            "by_asset_class": public_deeds_by_class,
        },
    }
