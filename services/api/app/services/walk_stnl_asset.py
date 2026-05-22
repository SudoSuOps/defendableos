"""Walk single-tenant net-lease (STNL) CRE assets through the deed pipeline.

A parameterized walker for real STNL deals: a tenant on a long-term
NNN lease in a single-tenant property. Produces a Defendable Property
Record with OPERATOR_STATED_STNL_TERMS · the operator's stated NOI,
cap rate, market rent, term, and asking price travel publicly with
clear "Operator-stated · not a validated underwriting conclusion"
doctrine labels.

Doctrine: NOI is derived from `gla_sf × market_rent_per_sf_nnn_usd`
on the operator's stated rent-roll basis. Cap rate, term, lease
structure are operator claims. The number is publicly visible so
buyers can evaluate the deal economics, but the doctrine label is
always attached. Validator review is required before any of these
fields can be upgraded to a validated conclusion.

Run from the Fly machine:
    SPEC=wawa_fl    python -m app.services.walk_stnl_asset
    SPEC=amazon_dc  python -m app.services.walk_stnl_asset
    SPEC=all        python -m app.services.walk_stnl_asset
"""
from __future__ import annotations

import json
import os
import sys
import uuid
from dataclasses import dataclass

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


@dataclass
class StnlAssetSpec:
    asset_reference: str
    name: str                    # public display name
    description: str

    tenant_name: str             # "Wawa" / "Amazon"
    tenant_credit_note: str      # "Investment-grade equivalent (private credit)" / "Investment grade (AA-)"
    property_type: str           # "STNL_RETAIL_CONVENIENCE_AND_FUEL" / "STNL_INDUSTRIAL_LAST_MILE_DC"
    category: str                # human-readable category for Asset.category

    market: str                  # "South Florida · I-95 retail corridor"

    gla_sf: int                  # 6049 / 1000000
    market_rent_per_sf_nnn_usd: float  # 55.0 / 8.5
    lease_structure: str         # "Absolute NNN" / "Triple Net (NNN)"
    term_years: int              # 20
    options_summary: str         # "Four (4) five-year options"
    cap_rate_pct: float          # 5.0

    research_query: str          # Brave context query

    @property
    def noi_usd(self) -> int:
        return int(round(self.gla_sf * self.market_rent_per_sf_nnn_usd))

    @property
    def asking_price_usd(self) -> int:
        # asking = NOI / cap_rate · cap_rate is in percent, so divide by 100
        return int(round(self.noi_usd / (self.cap_rate_pct / 100.0)))


# ── Pre-defined specs ────────────────────────────────────────────────
SPECS: dict[str, StnlAssetSpec] = {
    "wawa_fl": StnlAssetSpec(
        asset_reference="DOV-CRE-STNL-WAWA-000001",
        name="Wawa STNL · South Florida",
        description=(
            "Single-tenant net-lease convenience-and-fuel retail · "
            "Wawa-prototype free-standing store · South Florida "
            "I-95 retail corridor · 20-year base term · absolute NNN "
            "structure · operator-owned · marketing preview only."
        ),
        tenant_name="Wawa",
        tenant_credit_note="Privately-held national operator · institutional credit profile",
        property_type="STNL_RETAIL_CONVENIENCE_AND_FUEL",
        category="STNL_RETAIL",
        market="South Florida · I-95 retail corridor",
        gla_sf=6_049,
        market_rent_per_sf_nnn_usd=55.0,
        lease_structure="Absolute NNN",
        term_years=20,
        options_summary="Four (4) five-year renewal options",
        cap_rate_pct=5.0,
        research_query="Wawa STNL net lease retail South Florida 5 cap 2026",
    ),
    "amazon_dc": StnlAssetSpec(
        asset_reference="DOV-CRE-STNL-AMAZON-000001",
        name="Amazon Last-Mile DC · STNL",
        description=(
            "Single-tenant net-lease industrial last-mile distribution "
            "center · Amazon as sole tenant · ~1,000,000 SF · 20-year "
            "base term · Triple Net (NNN) lease structure · "
            "operator-owned · marketing preview only."
        ),
        tenant_name="Amazon",
        tenant_credit_note="Investment grade (S&P AA · Moody's A1)",
        property_type="STNL_INDUSTRIAL_LAST_MILE_DC",
        category="STNL_INDUSTRIAL",
        market="South Florida · Medley/Doral last-mile cluster",
        gla_sf=1_000_000,
        market_rent_per_sf_nnn_usd=8.50,
        lease_structure="Triple Net (NNN)",
        term_years=20,
        options_summary="Two (2) ten-year renewal options",
        cap_rate_pct=5.0,
        research_query="Amazon last mile distribution center NNN STNL industrial 5 cap 2026",
    ),
}


def _build_evidence_payload(spec: StnlAssetSpec) -> dict:
    """Operator-stated evidence summary for the STNL asset.

    Doctrine: this is an illustrative pre-engagement evidence summary.
    Real engagement workflows attach actual lease abstracts, rent roll
    PDFs, environmental reports, etc. as separate evidence items.
    """
    return {
        "evidence_type": "STNL_DEAL_TERMS_SUMMARY",
        "asset_reference": spec.asset_reference,
        "tenant": {
            "name": spec.tenant_name,
            "credit_note": spec.tenant_credit_note,
        },
        "property": {
            "property_type": spec.property_type,
            "category": spec.category,
            "market": spec.market,
            "gla_sf": spec.gla_sf,
        },
        "lease_terms": {
            "structure": spec.lease_structure,
            "base_term_years": spec.term_years,
            "options_summary": spec.options_summary,
            "market_rent_per_sf_nnn_usd": spec.market_rent_per_sf_nnn_usd,
            "rent_basis": "MARKET_RATE_OPERATOR_STATED",
        },
        "computed": {
            "noi_usd": spec.noi_usd,
            "noi_basis": "gla_sf × market_rent_per_sf_nnn_usd",
            "cap_rate_pct": spec.cap_rate_pct,
            "asking_price_usd": spec.asking_price_usd,
            "asking_basis": "noi_usd / (cap_rate_pct / 100)",
        },
        "missing_evidence_for_real_engagement": [
            "EXECUTED_LEASE_ABSTRACT",
            "RENT_ROLL_PDF",
            "ESTOPPEL_CERTIFICATE",
            "SNDA",
            "ENVIRONMENTAL_PHASE_I",
            "PROPERTY_CONDITION_REPORT",
            "TITLE_COMMITMENT",
            "SURVEY_AND_SITE_PLAN",
            "T-12_OPERATING_HISTORY",
        ],
        "captured_at": "2026-05-22T22:00:00Z",
        "captured_by": "defendable-cre · stnl-walker",
    }


def _get_demo_user_org(db: Session) -> tuple[User, Organization]:
    user = db.query(User).filter(User.email.like("%swarmandbee.ai")).first()
    if not user:
        raise RuntimeError("Seed user not found · run base seed first.")
    org = db.query(Organization).filter(Organization.slug == "swarmbee").first()
    if not org:
        raise RuntimeError("Demo org not found · run base seed first.")
    return user, org


def _ensure_asset(db: Session, org: Organization, user: User, spec: StnlAssetSpec) -> Asset:
    asset = (
        db.query(Asset)
        .filter(
            Asset.organization_id == org.id,
            Asset.public_asset_reference == spec.asset_reference,
        )
        .first()
    )
    if asset:
        return asset
    asset = Asset(
        id=uuid.uuid4(),
        organization_id=org.id,
        public_asset_reference=spec.asset_reference,
        asset_class=AssetClass.REAL_ESTATE,
        category=spec.category,
        name=spec.name,
        description=spec.description,
        status=AssetStatus.EVIDENCE_INTAKE,
        client_internal_reference=f"STNL-{spec.asset_reference}",
        created_by=user.id,
    )
    db.add(asset)
    db.flush()
    return asset


def _ensure_evidence(db: Session, asset: Asset, user: User, spec: StnlAssetSpec) -> EvidenceItem:
    body = json.dumps(_build_evidence_payload(spec), indent=2, sort_keys=True).encode("utf-8")
    digest = sha256_bytes(body)
    existing = (
        db.query(EvidenceItem)
        .filter(EvidenceItem.asset_id == asset.id)
        .filter(EvidenceItem.sha256_hash == digest)
        .first()
    )
    if existing:
        return existing
    safe_ref = spec.asset_reference.lower().replace("-", "_")
    evidence = EvidenceItem(
        id=uuid.uuid4(),
        organization_id=asset.organization_id,
        asset_id=asset.id,
        filename=f"{safe_ref}_stnl_terms.json",
        storage_key=(
            f"organizations/{asset.organization_id}/assets/{asset.id}"
            f"/raw/{safe_ref}_stnl_terms.json"
        ),
        content_type="application/json",
        byte_size=len(body),
        evidence_type=EvidenceType.OTHER,
        visibility=Visibility.PRIVATE,
        ingestion_status=IngestionStatus.INDEXED,
        sha256_hash=digest,
        uploaded_by=user.id,
        provenance="OPERATOR_DEAL_TERMS_SUMMARY",
    )
    db.add(evidence)
    db.flush()
    return evidence


def _live_brave_sector_context(query: str, max_sources: int = 5) -> list[dict]:
    """Sector-level Brave context · NOT property-specific."""
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
            "supports": "SECTOR_CONTEXT_ONLY",
            "evidence_classification": "MARKET_COMMENTARY",
            "warning": (
                "Per doctrine, sector market commentary is not a confirmed "
                "sale price for this specific asset and is not an "
                "underwriting conclusion."
            ),
        }
        for s in result.sources
    ]


def walk(spec: StnlAssetSpec, force_new_version: bool = False) -> dict:
    db: Session = SessionLocal()
    try:
        user, org = _get_demo_user_org(db)
        asset = _ensure_asset(db, org, user, spec)

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

        evidence = _ensure_evidence(db, asset, user, spec)
        print(f"  evidence indexed · sha256={evidence.sha256_hash[:16]}…")

        manifest = regenerate_manifest(db, asset)
        print(f"  manifest regenerated · sha256={manifest.manifest_sha256[:16]}…")

        print(f"  Brave sector context: {spec.research_query!r}")
        sector_context = _live_brave_sector_context(spec.research_query)
        print(f"  Brave returned {len(sector_context)} sector sources")

        prev_aiov = (
            db.query(AIOVAnalysis)
            .filter(AIOVAnalysis.asset_id == asset.id)
            .order_by(AIOVAnalysis.version.desc())
            .first()
        )
        next_aiov_version = (prev_aiov.version + 1) if prev_aiov else 1

        narrative = (
            f"Operator-stated single-tenant-net-lease (STNL) preview for "
            f"{spec.name}. Tenant: {spec.tenant_name} ({spec.tenant_credit_note}). "
            f"Property type: {spec.property_type}. Market: {spec.market}. "
            f"GLA: {spec.gla_sf:,} SF. Lease structure: {spec.lease_structure}. "
            f"Base term: {spec.term_years} years. Options: {spec.options_summary}. "
            f"Market rent: ${spec.market_rent_per_sf_nnn_usd:.2f} / SF NNN, "
            f"operator-stated basis. Net Operating Income (NOI), derived "
            f"as gla_sf × market_rent_per_sf_nnn_usd, is "
            f"${spec.noi_usd:,} USD. Operator cap rate: {spec.cap_rate_pct}%. "
            f"Operator asking price, derived as NOI / cap_rate, is "
            f"${spec.asking_price_usd:,} USD. "
            f"All figures are operator-stated · this is a draft marketing "
            f"preview, NOT a validator-issued underwriting conclusion, "
            f"professional appraisal, or confirmed-sale comparable. A real "
            f"engagement requires lease abstract review, rent roll "
            f"verification, and validator approval before any of these "
            f"figures may be elevated to a validated value claim."
        )

        aiov_payload = {
            "analysis_type": "DEFENDABLE_CRE_STNL_OPERATOR_STATED",
            "asset_reference": asset.public_asset_reference,
            "asset_class": asset.asset_class.value,
            "status": "GENERATED_FOR_DRAFT_MARKETING_DISPLAY",
            "intelligence_engine": "defendable-stnl-walker · operator-stated",
            "prompt_version": "stnl_walker.v1",
            "asset_profile": {
                "name": spec.name,
                "tenant_name": spec.tenant_name,
                "property_type": spec.property_type,
                "market": spec.market,
            },
            "evidence_basis": [
                {
                    "source_id": str(evidence.id),
                    "source_type": "PRIVATE_EVIDENCE",
                    "evidence_type": "STNL_DEAL_TERMS_SUMMARY",
                    "supports": "DEAL_ECONOMICS_OPERATOR_STATED",
                    "sha256": evidence.sha256_hash,
                }
            ],
            "market_commentary_sector": sector_context,
            "value_opinion": {
                "display_status": "OPERATOR_STATED_STNL_TERMS",
                "currency": "USD",
                # The structured STNL terms block · surfaced publicly by
                # _build_public_aiov_block when this display_status applies.
                "stnl_terms": {
                    "tenant_name": spec.tenant_name,
                    "tenant_credit_note": spec.tenant_credit_note,
                    "property_type": spec.property_type,
                    "gla_sf": spec.gla_sf,
                    "market_rent_per_sf_nnn_usd": spec.market_rent_per_sf_nnn_usd,
                    "lease_structure": spec.lease_structure,
                    "term_years": spec.term_years,
                    "options_summary": spec.options_summary,
                    "noi_usd": spec.noi_usd,
                    "cap_rate_pct": spec.cap_rate_pct,
                    "asking_price_usd": spec.asking_price_usd,
                    "currency": "USD",
                },
                "notes": (
                    "Operator-stated STNL deal terms. NOI is derived from "
                    "the operator's market-rate basis. Cap rate, term, and "
                    "lease structure are operator claims. A validated "
                    "underwriting conclusion requires lease abstract review, "
                    "rent roll verification, and validator approval."
                ),
            },
            "missing_evidence_for_real_engagement": [
                "EXECUTED_LEASE_ABSTRACT",
                "RENT_ROLL_PDF",
                "ESTOPPEL_CERTIFICATE",
                "SNDA",
                "ENVIRONMENTAL_PHASE_I",
                "PROPERTY_CONDITION_REPORT",
                "TITLE_COMMITMENT",
                "SURVEY_AND_SITE_PLAN",
                "T-12_OPERATING_HISTORY",
                "CONFIRMED_SALE_COMPARABLES",
            ],
            "limitations": [
                "Operator-stated terms only",
                "NOT a licensed appraisal",
                "NOT a warranty, certification, or authentication guarantee",
                "NOT a confirmed-sale comparable",
                "NOT a solicitation to acquire an interest in real property",
            ],
            "lifecycle_display": {
                "record_status_display": "DRAFT_MARKETING_PREVIEW",
                "validator_status_display": "PASSED_FOR_DRAFT_MARKETING_DISPLAY",
                "value_display_status": "OPERATOR_STATED_STNL_TERMS",
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
            narrative=narrative,
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
            "tenant_name": spec.tenant_name,
            "gla_sf": spec.gla_sf,
            "market_rent_per_sf_nnn_usd": spec.market_rent_per_sf_nnn_usd,
            "lease_structure": spec.lease_structure,
            "term_years": spec.term_years,
            "noi_usd": spec.noi_usd,
            "cap_rate_pct": spec.cap_rate_pct,
            "asking_price_usd": spec.asking_price_usd,
            "brave_sources": len(sector_context),
            "already_existed": False,
        }
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def _walk_all() -> dict:
    out = {}
    for key in ("wawa_fl", "amazon_dc"):
        print(f"\n══ walking STNL {key} ══")
        out[key] = walk(SPECS[key], force_new_version=False)
        print(json.dumps(out[key], indent=2, default=str))
    return out


if __name__ == "__main__":
    spec_key = os.environ.get("SPEC", "wawa_fl")
    force = os.environ.get("FORCE_NEW", "false").lower() in {"1", "true", "yes"}
    if spec_key == "all":
        _walk_all()
        sys.exit(0)
    if spec_key not in SPECS:
        print(f"Unknown SPEC={spec_key!r} · choose from: {list(SPECS.keys())} or 'all'")
        sys.exit(1)
    spec = SPECS[spec_key]
    print(f"═══ walking STNL {spec.asset_reference} · {spec.name} (force_new={force}) ═══")
    result = walk(spec, force_new_version=force)
    print("\n═══ result ═══")
    print(json.dumps(result, indent=2, default=str))
