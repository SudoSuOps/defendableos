"""Seed the Priority A Brand Outlet watchlist · idempotent.

Per the founder spec (2026-05-22), starting research lanes:
  Track A · ProductRadar now ·
    EcoFlow, Anker, CyberPower, Seagate, Western Digital,
    Logitech, DJI, DEWALT, Milwaukee, Makita
  Track B · high potential, higher controls · DEFER
    Gucci, Louis Vuitton, Chanel, Rolex, Omega, Cartier
    (authentication + authorized supply risk · do NOT seed dropship paths)

Every entry enters with sourcing_status=NOT_REVIEWED · platform never
claims a supplier authorization that hasn't been confirmed.
"""
from __future__ import annotations

import json
import uuid

from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.productradar import (
    BrandPriorityTier,
    BrandSourcingStatus,
    BrandWatchlist,
    MerchandisingLane,
    PolicyRiskFlag,
)


# Priority A · research-now brands
WATCHLIST_A: list[dict] = [
    {
        "slug": "ecoflow",
        "name": "EcoFlow",
        "lane": MerchandisingLane.HOME_POWER_EQUIPMENT,
        "notes": "Brand Outlet prominent · portable power stations · SwarmEnergy adjacency · premium ticket · visually marketable.",
    },
    {
        "slug": "anker",
        "name": "Anker",
        "lane": MerchandisingLane.LATEST_TECH,
        "notes": "Charging / portable power / tech accessories · strong ecommerce creative fit · tech-adjacent.",
    },
    {
        "slug": "cyberpower",
        "name": "CyberPower",
        "lane": MerchandisingLane.LATEST_TECH,
        "notes": "UPS / power protection · compute + small-business continuity adjacency.",
    },
    {
        "slug": "seagate",
        "name": "Seagate",
        "lane": MerchandisingLane.ELITE_TECH,
        "notes": "Storage · compute/workstation and NAS adjacency.",
    },
    {
        "slug": "western-digital",
        "name": "Western Digital",
        "lane": MerchandisingLane.ELITE_TECH,
        "notes": "Storage · compute/workstation and NAS adjacency.",
    },
    {
        "slug": "logitech",
        "name": "Logitech",
        "lane": MerchandisingLane.LATEST_TECH,
        "notes": "Workstation accessories · easy branded tech research lane.",
    },
    {
        "slug": "dji",
        "name": "DJI",
        "lane": MerchandisingLane.LATEST_TECH,
        "notes": "Cameras/drones · strong visual MarketReady opportunity · higher policy/logistics care.",
    },
    {
        "slug": "dewalt",
        "name": "DEWALT",
        "lane": MerchandisingLane.TOOLS_EQUIPMENT,
        "notes": "Tools · equipment/contractor vertical · Jupiter Power Wash adjacency.",
    },
    {
        "slug": "milwaukee",
        "name": "Milwaukee",
        "lane": MerchandisingLane.TOOLS_EQUIPMENT,
        "notes": "Tools · equipment/contractor vertical.",
    },
    {
        "slug": "makita",
        "name": "Makita",
        "lane": MerchandisingLane.TOOLS_EQUIPMENT,
        "notes": "Tools · equipment/contractor vertical.",
    },
]


# Priority DEFER · do NOT pursue without authorized supply + authentication
WATCHLIST_DEFER: list[dict] = [
    {
        "slug": "gucci",
        "name": "Gucci",
        "lane": MerchandisingLane.LUXURY_HANDBAGS,
        "notes": "DEFER · authentication + authorized supply risk · luxury counterfeit lane.",
    },
    {
        "slug": "louis-vuitton",
        "name": "Louis Vuitton",
        "lane": MerchandisingLane.LUXURY_HANDBAGS,
        "notes": "DEFER · authentication + authorized supply risk.",
    },
    {
        "slug": "chanel",
        "name": "Chanel",
        "lane": MerchandisingLane.LUXURY_HANDBAGS,
        "notes": "DEFER · authentication + authorized supply risk.",
    },
    {
        "slug": "rolex",
        "name": "Rolex",
        "lane": MerchandisingLane.LUXURY_WATCHES_JEWELRY,
        "notes": "DEFER · authentication + capital + condition risk.",
    },
    {
        "slug": "omega",
        "name": "Omega",
        "lane": MerchandisingLane.LUXURY_WATCHES_JEWELRY,
        "notes": "DEFER · authentication risk.",
    },
    {
        "slug": "cartier",
        "name": "Cartier",
        "lane": MerchandisingLane.LUXURY_WATCHES_JEWELRY,
        "notes": "DEFER · authentication risk.",
    },
]


def _ensure_brand(
    db: Session, spec: dict, priority: BrandPriorityTier, risk: PolicyRiskFlag
) -> BrandWatchlist:
    existing = (
        db.query(BrandWatchlist).filter(BrandWatchlist.brand_slug == spec["slug"]).first()
    )
    if existing:
        return existing
    row = BrandWatchlist(
        id=uuid.uuid4(),
        brand_slug=spec["slug"],
        brand_name=spec["name"],
        merchandising_lane=spec["lane"],
        priority_tier=priority,
        sourcing_status=BrandSourcingStatus.NOT_REVIEWED,
        policy_risk_flag=risk,
        notes=spec["notes"],
    )
    db.add(row)
    db.flush()
    return row


def seed_brand_outlet() -> dict:
    db: Session = SessionLocal()
    try:
        a = [
            _ensure_brand(db, s, BrandPriorityTier.A, PolicyRiskFlag.NONE)
            for s in WATCHLIST_A
        ]
        defer = [
            _ensure_brand(db, s, BrandPriorityTier.DEFER, PolicyRiskFlag.TRADEMARK_RISK)
            for s in WATCHLIST_DEFER
        ]
        db.commit()
        return {
            "priority_a_count": len(a),
            "priority_defer_count": len(defer),
            "priority_a_slugs": [b.brand_slug for b in a],
            "priority_defer_slugs": [b.brand_slug for b in defer],
            "sourcing_status_default": "NOT_REVIEWED",
        }
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print(json.dumps(seed_brand_outlet(), indent=2))
