"""Seed canonical-goods watchlist for Defendable Compute.

Idempotent. Reuses the existing seed user/org from app.services.seed.
Creates:
  1. CanonicalGood for the RTX PRO 6000 Blackwell, linked to the
     existing DOV-COMPUTE-000001 asset
  2. CanonicalGood entries for the rest of the compute watchlist
  3. Connector registry snapshots (status will be whatever current
     config supports · NOT_CONFIGURED or CONFIGURED_DISABLED in dev)
  4. SourceRightsRecord defaults for Brave + eBay (both
     INTERNAL_RESEARCH_ONLY · training_eligible=False)
  5. Draft CompSet for DOV-COMPUTE-000001 with NOT_READY status

Doctrine: NO fake market observations, NO fake transaction evidence,
NO fake sold prices. The seed builds the LOAD-BEARING SCAFFOLD ·
real data only enters via a controlled connector run.
"""
from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.asset import Asset
from app.models.organization import Organization
from app.models.user import User
from app.models.goods import (
    CanonicalGood,
    CompSet,
    CompSetIntendedUse,
    CompSetStatus,
    GoodsClass,
    IdentityStatus,
    ProviderName,
    RightsStatus,
    SourceRightsRecord,
    SourceConnector,
)
from app.services.connector_registry import refresh_all


COMPUTE_WATCHLIST: list[dict] = [
    {
        "goods_id": "GOOD-COMPUTE-NVIDIA-RTXPRO6000-BW-000001",
        "category": "GPU_ACCELERATOR",
        "manufacturer": "NVIDIA",
        "model": "RTX PRO 6000 Blackwell Workstation GPU",
        "canonical_title": "NVIDIA RTX PRO 6000 Blackwell Workstation GPU",
        "normalized_attributes": {
            "memory_gb": 96,
            "use_case": "PROFESSIONAL_AI_AND_ACCELERATED_COMPUTE",
            "form_factor": "WORKSTATION_GPU",
        },
        "primary_asset_reference": "DOV-COMPUTE-000001",
    },
    {
        "goods_id": "GOOD-COMPUTE-NVIDIA-RTX5090",
        "category": "GPU_ACCELERATOR",
        "manufacturer": "NVIDIA",
        "model": "GeForce RTX 5090",
        "canonical_title": "NVIDIA GeForce RTX 5090",
        "normalized_attributes": {
            "memory_gb": 32,
            "use_case": "ENTHUSIAST_AND_INFERENCE",
            "form_factor": "CONSUMER_GPU",
        },
    },
    {
        "goods_id": "GOOD-COMPUTE-NVIDIA-RTX4500-BW",
        "category": "GPU_ACCELERATOR",
        "manufacturer": "NVIDIA",
        "model": "RTX 4500 Blackwell",
        "canonical_title": "NVIDIA RTX 4500 Blackwell",
        "normalized_attributes": {
            "memory_gb": 32,
            "use_case": "WORKSTATION_AI_AND_RENDERING",
            "form_factor": "WORKSTATION_GPU",
        },
    },
    {
        "goods_id": "GOOD-COMPUTE-NVIDIA-V100-32GB",
        "category": "GPU_ACCELERATOR",
        "manufacturer": "NVIDIA",
        "model": "Tesla V100 32GB",
        "canonical_title": "NVIDIA Tesla V100 32GB",
        "normalized_attributes": {
            "memory_gb": 32,
            "use_case": "DATA_CENTER_TRAINING_LEGACY",
            "form_factor": "DATA_CENTER_GPU",
        },
    },
    {
        "goods_id": "GOOD-COMPUTE-AI-WORKSTATION-SYSTEM",
        "category": "AI_WORKSTATION",
        "manufacturer": "VARIOUS",
        "model": "AI Workstation / GPU Server",
        "canonical_title": "AI Workstation / GPU Server",
        "normalized_attributes": {
            "form_factor": "SYSTEM",
            "use_case": "AI_AND_HPC_WORKSTATION",
        },
    },
    {
        "goods_id": "GOOD-COMPUTE-DEFENDABLE-BOX",
        "category": "EDGE_INFERENCE",
        "manufacturer": "SWARM_AND_BEE",
        "model": "Defendable Box · Edge Inference Appliance",
        "canonical_title": "Defendable Box · Edge Inference Appliance",
        "normalized_attributes": {
            "form_factor": "EDGE_APPLIANCE",
            "use_case": "SOVEREIGN_EDGE_INFERENCE",
        },
    },
]


def _get_demo_user_org(db: Session) -> tuple[User, Organization]:
    user = db.query(User).filter(User.email.like("%swarmandbee.ai")).first()
    if not user:
        raise RuntimeError("Seed user not found · run base seed first.")
    org = db.query(Organization).filter(Organization.slug == "swarmbee").first()
    if not org:
        raise RuntimeError("Demo org not found · run base seed first.")
    return user, org


def _ensure_canonical_good(db: Session, spec: dict) -> CanonicalGood:
    existing = (
        db.query(CanonicalGood)
        .filter(CanonicalGood.goods_id == spec["goods_id"])
        .first()
    )
    if existing:
        return existing

    primary_asset_id = None
    if ref := spec.get("primary_asset_reference"):
        asset = (
            db.query(Asset).filter(Asset.public_asset_reference == ref).first()
        )
        if asset:
            primary_asset_id = asset.id

    good = CanonicalGood(
        id=uuid.uuid4(),
        goods_id=spec["goods_id"],
        goods_class=GoodsClass.COMPUTE_HARDWARE,
        category=spec["category"],
        manufacturer=spec["manufacturer"],
        model=spec["model"],
        canonical_title=spec["canonical_title"],
        normalized_attributes=spec["normalized_attributes"],
        identity_status=IdentityStatus.NORMALIZED_PENDING_REVIEW,
        primary_asset_id=primary_asset_id,
    )
    db.add(good)
    db.flush()
    return good


def _ensure_source_rights_defaults(
    db: Session, connector: SourceConnector
) -> SourceRightsRecord:
    """Brave + eBay get INTERNAL_RESEARCH_ONLY · training_eligible=False."""
    existing = (
        db.query(SourceRightsRecord)
        .filter(SourceRightsRecord.source_connector_id == connector.id)
        .first()
    )
    if existing:
        return existing
    rec = SourceRightsRecord(
        id=uuid.uuid4(),
        source_connector_id=connector.id,
        artifact_id=None,
        data_class="THIRD_PARTY_PUBLIC_RESEARCH",
        acquisition_method="DEFENDABLE_CONNECTOR_RUN",
        rights_status=RightsStatus.INTERNAL_RESEARCH_ONLY,
        training_eligible=False,
        public_display_eligible=False,
        retention_policy="30_DAY_ROLLING",
        review_notes="Default rights for trend-discovery / market-observation connectors.",
    )
    db.add(rec)
    db.flush()
    return rec


def _ensure_draft_comp_set(db: Session, good: CanonicalGood, asset: Asset | None) -> CompSet:
    comp_set_id = f"COMPSET-{asset.public_asset_reference if asset else good.goods_id}-v1"
    existing = db.query(CompSet).filter(CompSet.comp_set_id == comp_set_id).first()
    if existing:
        return existing
    cs = CompSet(
        id=uuid.uuid4(),
        comp_set_id=comp_set_id,
        goods_id=good.id,
        asset_id=asset.id if asset else None,
        title=f"{good.canonical_title} · market context comp set",
        intended_use=CompSetIntendedUse.MARKET_CONTEXT_RESEARCH,
        comp_set_status=CompSetStatus.NOT_READY_FOR_VALUE_SUPPORT,
        grade_summary={"A": 0, "B": 0, "C": 0, "D": 0, "E": 0},
        limitations=["NO_CONFIRMED_TRANSACTION_EVIDENCE"],
        confirmed_transaction_count=0,
        active_listing_count=0,
        trend_signal_count=0,
        validator_status=None,
    )
    db.add(cs)
    db.flush()
    return cs


def seed_goods() -> dict:
    db: Session = SessionLocal()
    try:
        user, org = _get_demo_user_org(db)
        _ = user  # currently unused · reserved for future audit-event hooks

        # 1. Connector registry · safe statuses derived from current config
        connectors = refresh_all(db)
        brave_conn = next(
            (c for c in connectors if c.provider_name == ProviderName.BRAVE_LLM_CONTEXT),
            None,
        )
        ebay_conn = next(
            (c for c in connectors if c.provider_name == ProviderName.EBAY_BROWSE),
            None,
        )

        # 2. Default source-rights records for the third-party connectors
        if brave_conn:
            _ensure_source_rights_defaults(db, brave_conn)
        if ebay_conn:
            _ensure_source_rights_defaults(db, ebay_conn)

        # 3. Canonical goods watchlist · 6 entries
        canonical_goods: list[CanonicalGood] = []
        for spec in COMPUTE_WATCHLIST:
            canonical_goods.append(_ensure_canonical_good(db, spec))

        # 4. Draft comp set for the primary asset (RTX PRO 6000)
        primary_good = next(
            (g for g in canonical_goods if "RTXPRO6000" in g.goods_id), None
        )
        primary_asset = (
            db.query(Asset)
            .filter(Asset.public_asset_reference == "DOV-COMPUTE-000001")
            .first()
        )
        cs = _ensure_draft_comp_set(db, primary_good, primary_asset) if primary_good else None

        db.commit()
        return {
            "canonical_goods_count": len(canonical_goods),
            "connectors_count": len(connectors),
            "primary_good": primary_good.goods_id if primary_good else None,
            "draft_comp_set": cs.comp_set_id if cs else None,
            "comp_set_status": cs.comp_set_status.value if cs else None,
        }
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    import json
    result = seed_goods()
    print(json.dumps(result, indent=2))
