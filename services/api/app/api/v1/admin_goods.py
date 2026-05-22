"""Admin · Goods Intelligence read endpoints.

Protected behind require_platform_admin. ALL endpoints in this turn
are READ-ONLY · the live-ingestion POSTs (POST /discover/brave,
POST /discover/ebay-browse) are intentionally NOT wired this turn
so no live provider call can fire before the founder-demo turn.

The admin frontend lane (next session) consumes these endpoints to
render the 9-screen Goods Intelligence admin module.
"""
from __future__ import annotations


from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_platform_admin
from app.models.goods import (
    ApprovedClaim,
    ArtifactRegistry,
    CanonicalGood,
    CompSet,
    DiscoveryRun,
    ItadPartner,
    MarketObservation,
    PairBatch,
    PartnerTransactionObservation,
    SourceConnector,
    SourceRightsRecord,
    TrainingPair,
    TrendSignal,
    TransactionEvidence,
)
from app.services.connector_registry import CONNECTOR_DEFINITIONS, resolve_status


router = APIRouter(prefix="/admin/goods")


# ───────────────────────────────────────────────────────────────────
# Overview · dashboard counts
# ───────────────────────────────────────────────────────────────────


@router.get("/overview")
def overview(
    db: Session = Depends(get_db),
    _admin=Depends(require_platform_admin),
) -> dict:
    """Honest counts for the Goods Intelligence overview dashboard."""
    return {
        "watched_goods": db.query(CanonicalGood).count(),
        "trend_signals": db.query(TrendSignal).count(),
        "public_listing_observations": (
            db.query(MarketObservation)
            .filter(MarketObservation.source_type == "PUBLIC_ACTIVE_LISTING")
            .count()
        ),
        "confirmed_transactions": (
            db.query(TransactionEvidence)
            .filter(TransactionEvidence.transaction_status == "CONFIRMED_WITH_EVIDENCE")
            .count()
        ),
        "draft_comp_sets": db.query(CompSet).count(),
        "pair_candidates": db.query(TrainingPair).count(),
        "approved_eval_pairs": (
            db.query(TrainingPair)
            .filter(TrainingPair.use_class == "EVAL_ONLY")
            .count()
        ),
        "training_eligible_pairs": (
            db.query(TrainingPair).filter(TrainingPair.training_eligible == True).count()  # noqa: E712
        ),
        "discovery_runs": db.query(DiscoveryRun).count(),
        "artifacts_registered": db.query(ArtifactRegistry).count(),
        "itad_partners": db.query(ItadPartner).count(),
        "itad_partners_in_conversation_or_better": (
            db.query(ItadPartner)
            .filter(ItadPartner.partnership_status.in_([
                "IN_CONVERSATION", "PILOT_AGREEMENT", "PRODUCTION_PARTNER",
            ]))
            .count()
        ),
        "partner_transaction_observations": db.query(PartnerTransactionObservation).count(),
    }


# ───────────────────────────────────────────────────────────────────
# Connectors · honest status
# ───────────────────────────────────────────────────────────────────


@router.get("/connectors")
def list_connectors(
    db: Session = Depends(get_db),
    _admin=Depends(require_platform_admin),
) -> list[dict]:
    """7 connectors · status derived from current config (not cached)."""
    rows = db.query(SourceConnector).all()
    out = []
    for d in CONNECTOR_DEFINITIONS:
        live_status = resolve_status(d["provider_name"])
        db_row = next((r for r in rows if r.provider_name == d["provider_name"]), None)
        out.append(
            {
                "provider_name": d["provider_name"].value,
                "purpose": d["connector_purpose"],
                "status": live_status.value,
                "terms_review_status": (
                    db_row.terms_review_status.value if db_row else "TERMS_REVIEW_PENDING"
                ),
                "live_calls_enabled": db_row.live_calls_enabled if db_row else False,
                "registered_at": db_row.created_at.isoformat() if db_row else None,
            }
        )
    return out


# ───────────────────────────────────────────────────────────────────
# Canonical goods · watchlist
# ───────────────────────────────────────────────────────────────────


@router.get("/canonical-goods")
def list_canonical_goods(
    db: Session = Depends(get_db),
    _admin=Depends(require_platform_admin),
) -> list[dict]:
    rows = (
        db.query(CanonicalGood)
        .order_by(CanonicalGood.goods_id)
        .all()
    )
    return [
        {
            "id": str(g.id),
            "goods_id": g.goods_id,
            "goods_class": g.goods_class.value,
            "category": g.category,
            "manufacturer": g.manufacturer,
            "model": g.model,
            "canonical_title": g.canonical_title,
            "identity_status": g.identity_status.value,
            "primary_asset_id": str(g.primary_asset_id) if g.primary_asset_id else None,
            "observation_count": (
                db.query(MarketObservation)
                .filter(MarketObservation.goods_id == g.id)
                .count()
            ),
            "comp_set_count": (
                db.query(CompSet).filter(CompSet.goods_id == g.id).count()
            ),
        }
        for g in rows
    ]


# ───────────────────────────────────────────────────────────────────
# Comp sets · grading + readiness
# ───────────────────────────────────────────────────────────────────


@router.get("/comp-sets")
def list_comp_sets(
    db: Session = Depends(get_db),
    _admin=Depends(require_platform_admin),
) -> list[dict]:
    rows = db.query(CompSet).order_by(CompSet.comp_set_id).all()
    return [
        {
            "id": str(cs.id),
            "comp_set_id": cs.comp_set_id,
            "title": cs.title,
            "intended_use": cs.intended_use.value,
            "comp_set_status": cs.comp_set_status.value,
            "confirmed_transaction_count": cs.confirmed_transaction_count,
            "active_listing_count": cs.active_listing_count,
            "trend_signal_count": cs.trend_signal_count,
            "grade_summary": cs.grade_summary,
            "limitations": cs.limitations,
        }
        for cs in rows
    ]


@router.get("/comp-sets/{comp_set_id}")
def get_comp_set_readiness(
    comp_set_id: str,
    db: Session = Depends(get_db),
    _admin=Depends(require_platform_admin),
) -> dict:
    from app.services.comp_foundry import (
        comp_set_receipt_payload,
        validate_comp_set_readiness,
    )

    cs = db.query(CompSet).filter(CompSet.comp_set_id == comp_set_id).first()
    if cs is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "comp_set not found")

    readiness = validate_comp_set_readiness(db, cs.id)
    receipt = comp_set_receipt_payload(db, cs.id)
    return {
        "comp_set": receipt,
        "readiness": {
            "ready": readiness.ready,
            "status": readiness.status.value,
            "required_disclosure": readiness.required_disclosure,
            "reasons": readiness.reasons,
        },
    }


# ───────────────────────────────────────────────────────────────────
# Source rights ledger
# ───────────────────────────────────────────────────────────────────


@router.get("/source-rights")
def list_source_rights(
    db: Session = Depends(get_db),
    _admin=Depends(require_platform_admin),
) -> list[dict]:
    rows = db.query(SourceRightsRecord).all()
    return [
        {
            "id": str(r.id),
            "source_connector_id": str(r.source_connector_id) if r.source_connector_id else None,
            "artifact_id": str(r.artifact_id) if r.artifact_id else None,
            "data_class": r.data_class,
            "acquisition_method": r.acquisition_method,
            "rights_status": r.rights_status.value,
            "training_eligible": r.training_eligible,
            "public_display_eligible": r.public_display_eligible,
            "retention_policy": r.retention_policy,
            "review_notes": r.review_notes,
        }
        for r in rows
    ]


# ───────────────────────────────────────────────────────────────────
# Pair batches + training pairs
# ───────────────────────────────────────────────────────────────────


@router.get("/pair-batches")
def list_pair_batches(
    db: Session = Depends(get_db),
    _admin=Depends(require_platform_admin),
) -> list[dict]:
    rows = db.query(PairBatch).order_by(PairBatch.batch_id).all()
    return [
        {
            "id": str(b.id),
            "batch_id": b.batch_id,
            "goods_class": b.goods_class.value,
            "batch_type": b.batch_type.value,
            "batch_status": b.batch_status.value,
            "source_rights_status": b.source_rights_status.value,
            "training_eligible": b.training_eligible,
            "manifest_sha256": b.manifest_sha256,
            "pair_count": db.query(TrainingPair).filter(TrainingPair.pair_batch_id == b.id).count(),
        }
        for b in rows
    ]


# ───────────────────────────────────────────────────────────────────
# Approved claims · MarketReady gateway
# ───────────────────────────────────────────────────────────────────


@router.get("/approved-claims")
def list_approved_claims(
    db: Session = Depends(get_db),
    _admin=Depends(require_platform_admin),
) -> list[dict]:
    rows = db.query(ApprovedClaim).all()
    return [
        {
            "id": str(c.id),
            "asset_id": str(c.asset_id) if c.asset_id else None,
            "goods_id": str(c.goods_id) if c.goods_id else None,
            "claim_text": c.claim_text,
            "claim_type": c.claim_type,
            "public_permission": c.public_permission.value,
            "required_disclosure": c.required_disclosure,
            "applicable_surfaces": c.applicable_surfaces,
        }
        for c in rows
    ]


# ───────────────────────────────────────────────────────────────────
# ITAD partner-feed lane · the enterprise compute comp source
# ───────────────────────────────────────────────────────────────────


@router.get("/itad-partners")
def list_itad_partners(
    db: Session = Depends(get_db),
    _admin=Depends(require_platform_admin),
) -> list[dict]:
    """8 ITAD partners · honest partnership + agreement + rights state."""
    rows = db.query(ItadPartner).order_by(ItadPartner.slug).all()
    return [
        {
            "id": str(p.id),
            "slug": p.slug,
            "company_name": p.company_name,
            "company_url": p.company_url,
            "partnership_status": p.partnership_status.value,
            "compute_coverage_summary": p.compute_coverage_summary,
            "feed_format": p.feed_format.value,
            "agreement_status": p.agreement_status.value,
            "rights_scope": p.rights_scope.value,
            "contact_status": p.contact_status.value,
            "transaction_observation_count": (
                db.query(PartnerTransactionObservation)
                .filter(PartnerTransactionObservation.partner_id == p.id)
                .count()
            ),
        }
        for p in rows
    ]


# ───────────────────────────────────────────────────────────────────
# ProductRadar · demand intelligence read endpoints
# ───────────────────────────────────────────────────────────────────


@router.get("/productradar/overview")
def productradar_overview(
    db: Session = Depends(get_db),
    _admin=Depends(require_platform_admin),
) -> dict:
    """ProductRadar dashboard counts · all 0 until opportunities are added."""
    from app.models.productradar import (
        ConnectedStoreOutcome as CSO,
        KeywordDemandSignal as KDS,
        MarketplaceSalesResearch as MSR,
        OpportunityScoreReceipt as OSR,
        ProductOpportunity as PO,
        ShoppingPopularitySignal as SPS,
        SocialTrendSignal as STS,
        StoreIntelligenceObservation as SIO,
        SupplierCandidate as SC,
    )
    return {
        "product_opportunities": db.query(PO).count(),
        "watchlist": db.query(PO).filter(PO.status == "WATCHLIST").count(),
        "research_candidates": db.query(PO).filter(PO.status == "RESEARCH_CANDIDATE").count(),
        "marketready_candidates": db.query(PO).filter(PO.status == "MARKETREADY_CANDIDATE").count(),
        "launched": db.query(PO).filter(PO.status == "LAUNCHED").count(),
        "rejected": db.query(PO).filter(
            PO.status.in_([
                "REJECT_MARGIN_RISK", "REJECT_POLICY_RISK",
                "REJECT_OVERSATURATED", "REJECT_LOW_SIGNAL",
            ])
        ).count(),
        "keyword_demand_signals": db.query(KDS).count(),
        "shopping_popularity_signals": db.query(SPS).count(),
        "social_trend_signals": db.query(STS).count(),
        "store_intelligence_observations": db.query(SIO).count(),
        "marketplace_sales_researches": db.query(MSR).count(),
        "supplier_candidates": db.query(SC).count(),
        "connected_store_outcomes": db.query(CSO).count(),
        "opportunity_score_receipts": db.query(OSR).count(),
    }


@router.get("/productradar/opportunities")
def list_product_opportunities(
    db: Session = Depends(get_db),
    _admin=Depends(require_platform_admin),
) -> list[dict]:
    from app.models.productradar import ProductOpportunity as PO
    rows = db.query(PO).order_by(PO.latest_score.desc().nullslast()).all()
    return [
        {
            "id": str(o.id),
            "opportunity_id": o.opportunity_id,
            "product_name": o.product_name,
            "canonical_search_query": o.canonical_search_query,
            "category": o.category.value,
            "status": o.status.value,
            "recommendation": o.recommendation.value if o.recommendation else None,
            "latest_score": o.latest_score,
            "latest_score_at": o.latest_score_at.isoformat() if o.latest_score_at else None,
        }
        for o in rows
    ]


# ───────────────────────────────────────────────────────────────────
# DISCOVERY POST endpoints · DOCUMENTED ONLY · not wired this turn
# ───────────────────────────────────────────────────────────────────
# POST /admin/goods/discover/brave
# POST /admin/goods/discover/ebay-browse
#
# These two endpoints would gate on the kill switches in
# connector_registry, write a DiscoveryRun, call the provider ONCE,
# write the raw response to MARKET_OBSERVATIONS, normalize, and
# write an AuditEvent. They are NOT exposed in this turn so no
# live ingestion can fire accidentally · the next session enables
# them behind a separate kill switch.
