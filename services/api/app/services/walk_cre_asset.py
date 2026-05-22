"""Walk an illustrative CRE asset through the deed pipeline.

DOV-CRE-DEMO-000001 · Palm Grove Marketplace · a clearly-illustrative
grocery-anchored neighborhood retail center used to demonstrate the
Defendable CRE MarketReady product. Mirrors walk_compute_asset.py but
for the REAL_ESTATE asset class · uses the SAME doctrine guards · adds
NO new tables and NO schema migrations.

The CRE-specific structured payload (property metrics, tenant mix,
approved-claims library, MarketReady package status) lives entirely
inside the AIOV.analysis_json and gets carried through to the public
deed JSON. The frontend reads asset-class-aware display copy off the
deed_json's `record_status_display` / `validator_status_display` /
`value_display_status` fields, while the canonical DB enums stay at
their existing values so existing doctrine guards (is_draft_deed,
render_public_preview, validator_checks) are not weakened.

Run from the Fly machine:
    python -m app.services.walk_cre_asset
"""
from __future__ import annotations

import json
import uuid

from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.integrations import brave_llm_context
from app.models.ai import AIOVAnalysis, AIOVStatus
from app.models.asset import Asset, AssetClass, AssetStatus
from app.models.deed import DefendableDeed
from app.models.evidence import (
    EvidenceItem,
    EvidenceType,
    IngestionStatus,
    Visibility,
)
from app.models.organization import Organization
from app.models.user import User
from app.models.validator import ValidatorReview, ValidatorStatus
from app.services.deed import create_deed, publish_public
from app.services.hashing import sha256_bytes
from app.services.manifest import regenerate_manifest
from app.services.validator_checks import (
    build_receipt,
    run_deterministic_checks,
    summarise,
)


_ASSET_REF = "DOV-CRE-DEMO-000001"
_ASSET_NAME = "Palm Grove Marketplace"

_PROPERTY_FACTS = {
    "asset_class": "COMMERCIAL_REAL_ESTATE",
    "property_type": "GROCERY_ANCHORED_NEIGHBORHOOD_RETAIL",
    "market": "South Florida",
    "gross_leasable_area_sf": 82_400,
    "occupancy_pct": 94.2,
    "tenant_spaces": 14,
    "year_built": 2016,
    "year_renovated": 2024,
    "parking_ratio_per_1000_sf": 4.7,
    "parcel_size_acres": 9.8,
    "label": "ILLUSTRATIVE_DEMO_DATA",
}

_TENANT_MIX = [
    {"category": "Anchor Grocer", "sf": 38_000, "share_pct": 46.1, "category_class": "ANCHOR"},
    {"category": "Fitness Studio", "sf": 7_500, "share_pct": 9.1, "category_class": "INLINE"},
    {"category": "Fast Casual Dining", "sf": 3_200, "share_pct": 3.9, "category_class": "INLINE"},
    {"category": "Coffee Retailer", "sf": 2_100, "share_pct": 2.5, "category_class": "INLINE"},
    {"category": "Medical / Wellness", "sf": 4_500, "share_pct": 5.5, "category_class": "INLINE"},
    {"category": "Local Services + flex", "sf": 27_100, "share_pct": 32.9, "category_class": "INLINE"},
]

_APPROVED_CLAIMS = {
    "PUBLIC_SAFE_APPROVED_FOR_DEMO": [
        "Palm Grove Marketplace is an illustrative demo property.",
        "Asset class: Commercial Real Estate.",
        "Property type concept: Grocery-Anchored Neighborhood Retail Center.",
        "All displayed metrics are illustrative demo data.",
        "Draft proof record exists for demonstration.",
    ],
    "PUBLIC_SAFE_WITH_DISCLOSURE": [
        "Displayed size, occupancy, tenant mix and property facts, only when shown with the Illustrative Demo Data label.",
    ],
    "BLOCKED_FROM_PUBLIC_MARKETING": [
        "Final value conclusion",
        "Offering price",
        "Cap rate",
        "NOI",
        "Investment returns",
        "Actual tenant credit claims",
        "Certified property condition",
        "Appraisal conclusion",
        "Issued deed",
        "ENS publication",
    ],
}

_MARKETREADY_PACKAGE = {
    "status": "DRAFT_MARKETING_PACKAGE",
    "deliverables": {
        "property_website": "DRAFT_PREVIEW_READY",
        "teaser_sheet": "DRAFT_PREVIEW_READY",
        "offering_memorandum": "DRAFT_PREVIEW_READY",
        "buyer_room": "DEMO_PREVIEW_READY",
        "campaign_media_kit": "FUTURE_CAPABILITY",
        "listing_export_package": "FUTURE_CAPABILITY",
        "draft_proof_record": "REVIEW_REQUIRED",
    },
}

_NARRATIVE = (
    "This is an illustrative Defendable CRE product demonstration prepared "
    "to show how DefendableOS supports a commercial real estate go-to-market "
    "workflow. The subject is a sample grocery-anchored neighborhood retail "
    "center concept located in South Florida. All property metrics, tenant "
    "categories, occupancy levels and market positioning shown are "
    "illustrative demo data only and are not derived from a real asset, a "
    "real offering, an executed lease abstract, an appraisal, or a "
    "broker-provided rent roll. No final valuation, offering price, cap "
    "rate, NOI projection, or investment return is represented. The draft "
    "proof record produced for this preview travels with status "
    "DRAFT_MARKETING_PREVIEW and demonstrates how approved claims, "
    "validator review, evidence manifest references, and a draft "
    "Defendable Property Record can support a credible, scrutinable "
    "marketing presentation. This record is not a licensed appraisal, not "
    "a warranty, not a certification, and is not a solicitation to acquire "
    "an interest in real property."
)


def _build_evidence_payload() -> dict:
    """Synthetic but doctrine-correct illustrative evidence packet.

    This is NOT real property evidence · the packet structure is meant to
    show the SHAPE a real engagement would produce while making it
    obvious to any reviewer that the contents are illustrative.
    """
    return {
        "evidence_type": "ILLUSTRATIVE_PROPERTY_PACKET",
        "asset_reference": _ASSET_REF,
        "label": "ILLUSTRATIVE_DEMO_DATA",
        "property_facts": _PROPERTY_FACTS,
        "tenant_mix": _TENANT_MIX,
        "private_evidence_available": False,
        "public_disclosure": "DEMO_DATA_ONLY",
        "evidence_categories_demonstrated": [
            "PROPERTY_PHOTOS_AND_RENDERS",
            "SURVEY_SITE_PLAN_REFERENCE",
            "RENT_ROLL_ABSTRACT_REFERENCE",
            "LEASE_ABSTRACT_REFERENCE",
            "MARKET_RESEARCH_GROUNDING",
        ],
        "captured_at": "2026-05-22T22:00:00Z",
        "captured_by": "defendable-cre · marketready-demo-pipeline",
    }


def _get_demo_user_org(db: Session) -> tuple[User, Organization]:
    user = db.query(User).filter(User.email.like("%swarmandbee.ai")).first()
    if not user:
        raise RuntimeError("Seed user not found · run base seed first.")
    org = db.query(Organization).filter(Organization.slug == "swarmbee").first()
    if not org:
        raise RuntimeError("Demo org not found · run base seed first.")
    return user, org


def _ensure_asset(db: Session, org: Organization, user: User) -> Asset:
    asset = (
        db.query(Asset)
        .filter(
            Asset.organization_id == org.id,
            Asset.public_asset_reference == _ASSET_REF,
        )
        .first()
    )
    if asset:
        return asset
    asset = Asset(
        id=uuid.uuid4(),
        organization_id=org.id,
        public_asset_reference=_ASSET_REF,
        asset_class=AssetClass.REAL_ESTATE,
        category="GROCERY_ANCHORED_NEIGHBORHOOD_RETAIL",
        name=_ASSET_NAME,
        description=(
            "Illustrative Defendable CRE demo property. Grocery-anchored "
            "neighborhood retail center concept located in South Florida. "
            "All metrics, tenant categories and market data are "
            "illustrative demo data. Not an active offering. Not a real "
            "property listing. Not an appraisal, certification, or "
            "investment opportunity."
        ),
        status=AssetStatus.EVIDENCE_INTAKE,
        client_internal_reference=f"DEMO-{_ASSET_REF}",
        created_by=user.id,
    )
    db.add(asset)
    db.flush()
    return asset


def _ensure_evidence(db: Session, asset: Asset, user: User) -> EvidenceItem:
    body = json.dumps(_build_evidence_payload(), indent=2, sort_keys=True).encode("utf-8")
    digest = sha256_bytes(body)
    existing = (
        db.query(EvidenceItem)
        .filter(EvidenceItem.asset_id == asset.id)
        .filter(EvidenceItem.sha256_hash == digest)
        .first()
    )
    if existing:
        return existing
    evidence = EvidenceItem(
        id=uuid.uuid4(),
        organization_id=asset.organization_id,
        asset_id=asset.id,
        filename="palm_grove_illustrative_packet.json",
        storage_key=(
            f"organizations/{asset.organization_id}/assets/{asset.id}"
            f"/raw/palm_grove_illustrative_packet.json"
        ),
        content_type="application/json",
        byte_size=len(body),
        evidence_type=EvidenceType.OTHER,
        visibility=Visibility.PRIVATE,
        ingestion_status=IngestionStatus.INDEXED,
        sha256_hash=digest,
        uploaded_by=user.id,
        provenance="ILLUSTRATIVE_DEMO_PACKET",
    )
    db.add(evidence)
    db.flush()
    return evidence


def _live_brave_market_context(query: str, max_sources: int = 5) -> list[dict]:
    result = brave_llm_context.search(
        query=query,
        maximum_number_of_urls=max_sources,
        maximum_number_of_tokens=1024,
    )
    if result.status != "COMPLETED":
        return []
    return [
        {
            "source_id": f"BRAVE-{uuid.uuid4().hex[:8]}",
            "source_type": "PUBLIC_RESEARCH",
            "url": s.url,
            "title": s.title,
            "domain": s.domain,
            "supports": "MARKET_CONTEXT_ONLY",
            "evidence_classification": "MARKET_COMMENTARY",
            "warning": (
                "Per doctrine, market commentary is not a confirmed sale and "
                "is not an underwriting conclusion. The illustrative demo "
                "asset is not a real property; these sources contextualize "
                "the South Florida grocery-anchored retail SECTOR only."
            ),
        }
        for s in result.sources
    ]


def walk(force_new_version: bool = False) -> dict:
    db: Session = SessionLocal()
    try:
        user, org = _get_demo_user_org(db)
        asset = _ensure_asset(db, org, user)

        if not force_new_version:
            existing = (
                db.query(DefendableDeed)
                .filter(DefendableDeed.asset_id == asset.id)
                .filter(DefendableDeed.is_public == True)  # noqa: E712
                .order_by(DefendableDeed.version.desc())
                .first()
            )
            if existing:
                return {
                    "asset_reference": asset.public_asset_reference,
                    "deed_reference": existing.deed_reference,
                    "public_slug": existing.public_slug,
                    "record_hash": existing.record_hash,
                    "status": existing.status.value,
                    "already_existed": True,
                }

        evidence = _ensure_evidence(db, asset, user)
        print(f"  evidence indexed · sha256={evidence.sha256_hash[:16]}…")

        manifest = regenerate_manifest(db, asset)
        print(f"  manifest regenerated · sha256={manifest.manifest_sha256[:16]}…")

        # Optional · pull sector-level Brave context (NOT property-specific,
        # since the property is illustrative). Stored on the deed as
        # market_commentary_sector for transparency.
        print("  calling Brave for South Florida grocery-anchored retail context …")
        market_context = _live_brave_market_context(
            "South Florida grocery-anchored neighborhood retail center market 2026"
        )
        print(f"  Brave returned {len(market_context)} sector sources")

        # Determine next AIOV version (avoid v=1 tie · same pattern as compute walker)
        prev_aiov = (
            db.query(AIOVAnalysis)
            .filter(AIOVAnalysis.asset_id == asset.id)
            .order_by(AIOVAnalysis.version.desc())
            .first()
        )
        next_aiov_version = (prev_aiov.version + 1) if prev_aiov else 1

        aiov_payload = {
            "analysis_type": "DEFENDABLE_CRE_MARKETREADY_DEMO",
            "asset_reference": asset.public_asset_reference,
            "asset_class": asset.asset_class.value,
            "status": "GENERATED_FOR_DRAFT_MARKETING_DISPLAY",
            "intelligence_engine": "defendable-cre-walker · illustrative",
            "prompt_version": "cre_marketready_demo.v1",
            "asset_profile": {
                "name": _ASSET_NAME,
                "property_type": _PROPERTY_FACTS["property_type"],
                "market": _PROPERTY_FACTS["market"],
                "illustrative_demo": True,
            },
            "property_facts": _PROPERTY_FACTS,
            "tenant_mix": _TENANT_MIX,
            "evidence_basis": [
                {
                    "source_id": str(evidence.id),
                    "source_type": "PRIVATE_EVIDENCE",
                    "evidence_type": "ILLUSTRATIVE_PROPERTY_PACKET",
                    "supports": "ASSET_CONTEXT",
                    "sha256": evidence.sha256_hash,
                    "label": "ILLUSTRATIVE_DEMO_DATA",
                }
            ],
            "market_commentary_sector": market_context,
            "marketready_package": _MARKETREADY_PACKAGE,
            "approved_claims_library": _APPROVED_CLAIMS,
            "value_opinion": {
                "display_status": "NO_FINAL_VALUATION_REPRESENTED",
                "currency": "USD",
                "range_low": None,
                "range_high": None,
                "notes": (
                    "This is an illustrative product demonstration. No final "
                    "valuation, offering price, cap rate, NOI, return projection, "
                    "or investment opinion is represented. A real engagement "
                    "would require underwriting verification and validator "
                    "review before any value claim could be made public."
                ),
            },
            "missing_evidence_for_real_engagement": [
                "ACTUAL_RENT_ROLL",
                "LEASE_ABSTRACTS",
                "SURVEY_AND_CERTIFIED_SITE_PLAN",
                "ENVIRONMENTAL_REPORTS",
                "PROPERTY_CONDITION_REPORT",
                "T-12_OPERATING_HISTORY",
                "CONFIRMED_SALE_COMPARABLES",
                "TITLE_AND_INSURANCE",
            ],
            "limitations": [
                "Illustrative product demonstration only",
                "Not a licensed appraisal",
                "Not a warranty, certification, or authentication guarantee",
                "Not a solicitation to acquire an interest in real property",
            ],
            # Asset-class-aware DISPLAY strings (frontend reads these for
            # CRE-appropriate copy · DB enums stay at their existing values).
            "lifecycle_display": {
                "record_status_display": "DRAFT_MARKETING_PREVIEW",
                "validator_status_display": "PASSED_FOR_DRAFT_MARKETING_DISPLAY",
                "value_display_status": "NO_FINAL_VALUATION_REPRESENTED",
                "ens_status_display": "RESERVED_NOT_ISSUED",
                "publication_status_display": "NOT_PUBLISHED",
            },
        }

        aiov = AIOVAnalysis(
            id=uuid.uuid4(),
            asset_id=asset.id,
            version=next_aiov_version,
            status=AIOVStatus.GENERATED_FOR_VALIDATOR_REVIEW,
            analysis_json=aiov_payload,
            narrative=_NARRATIVE,
            supporting_source_ids=[str(evidence.id)],
            missing_evidence_json={
                "missing_evidence_types": aiov_payload["missing_evidence_for_real_engagement"],
            },
        )
        db.add(aiov)
        db.flush()

        results = run_deterministic_checks(db, asset, aiov)
        status_value = summarise(results)
        receipt = build_receipt(asset, aiov.version, results, status_value)
        review = ValidatorReview(
            id=uuid.uuid4(),
            asset_id=asset.id,
            aiov_analysis_id=aiov.id,
            version=next_aiov_version,
            status=ValidatorStatus(status_value),
            protocol="VALIDATE_THE_VALIDATOR",
            findings_json=receipt.get("blocking_findings", []),
            checks_json=receipt["checks"],
            receipt_sha256=receipt["receipt_sha256"],
            reviewed_by=user.id,
        )
        db.add(review)
        db.flush()
        print(f"  validator: {status_value}")

        if status_value != "PASSED_FOR_PACKAGING":
            db.commit()
            return {
                "asset_reference": asset.public_asset_reference,
                "deed_reference": None,
                "public_slug": None,
                "record_hash": None,
                "validator_status": status_value,
                "blocking_findings": receipt.get("blocking_findings", []),
                "already_existed": False,
            }

        deed = create_deed(db, asset, issued_by_user_id=user.id)
        publish_public(deed)
        db.commit()

        return {
            "asset_reference": asset.public_asset_reference,
            "deed_reference": deed.deed_reference,
            "public_slug": deed.public_slug,
            "record_hash": deed.record_hash,
            "validator_status": status_value,
            "narrative_length": len(_NARRATIVE),
            "marketready_status": _MARKETREADY_PACKAGE["status"],
            "brave_sources": len(market_context),
            "already_existed": False,
        }
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    import os
    force = os.environ.get("FORCE_NEW", "false").lower() in {"1", "true", "yes"}
    print(f"═══ walking {_ASSET_REF} · {_ASSET_NAME} (force_new={force}) ═══")
    result = walk(force_new_version=force)
    print("\n═══ result ═══")
    print(json.dumps(result, indent=2, default=str))
