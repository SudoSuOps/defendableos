"""Defendable ProductRadar · opportunity scoring service.

The 8-component weighted opportunity score per the founder spec:

  search_demand_growth          20%
  social_trend_velocity         15%
  marketplace_sold_signal       20%
  competitive_saturation        10%   (inverted · low is good)
  gross_margin_feasibility      15%
  shipping_returns_risk         10%   (inverted)
  brand_creative_fit             5%
  policy_compliance_risk         5%   (inverted)
  ─────────────────────────────────
  total                        100%

Doctrine guards encoded at the service boundary:

  · NEVER promote a product to LAUNCH_READY without at least one
    PERMISSIONED_CONNECTED_SALE or FIRST_PARTY_DEFENDABLE_SALE signal
  · NEVER let a SignalClass aggregation imply a confirmed-sale claim
    in any output payload · the receipt declares the source mix
  · A REJECT_POLICY_RISK flag overrides any positive score · the
    recommendation is REJECT regardless of total_score
  · Receipts are deterministic and SHA-256-hashed so the same inputs
    produce the same total_score every time
"""
from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.productradar import (
    CompetitionLevel,
    ConnectedStoreOutcome,
    KeywordDemandSignal,
    KeywordSearchVolumeTrend,
    MarketplaceSalesResearch,
    MarginScenario,
    OpportunityRecommendation,
    OpportunityScoreReceipt,
    PolicyRiskFlag,
    ProductOpportunity,
    ShoppingPopularitySignal,
    SignalClass,
    SocialTrendSignal,
    StoreIntelligenceObservation,
    SupplierCandidate,
    SupplierFeasibility,
)


# ────────────────────────────────────────────────────────────────────
#  Weight matrix · doctrine constant
# ────────────────────────────────────────────────────────────────────

SCORING_VERSION = "v1"

WEIGHTS: dict[str, float] = {
    "search_demand_growth": 0.20,
    "social_trend_velocity": 0.15,
    "marketplace_sold_signal": 0.20,
    "competitive_saturation": 0.10,        # inverted
    "gross_margin_feasibility": 0.15,
    "shipping_returns_risk": 0.10,         # inverted
    "brand_creative_fit": 0.05,
    "policy_compliance_risk": 0.05,        # inverted
}

# Confirmed-sale signal classes · only these may underwrite a
# LAUNCH_READY recommendation.
CONFIRMED_SALE_SIGNAL_CLASSES = {
    SignalClass.PERMISSIONED_CONNECTED_SALE,
    SignalClass.FIRST_PARTY_DEFENDABLE_SALE,
}


class ProductRadarError(ValueError):
    """Doctrine violation · raised at service boundary."""


# ────────────────────────────────────────────────────────────────────
#  Component scorers · each returns a value in [0.0, 1.0]
# ────────────────────────────────────────────────────────────────────


def _score_search_demand(signals: list[KeywordDemandSignal]) -> float:
    """Higher score when search volume is rising + meaningful absolute."""
    if not signals:
        return 0.0
    best = 0.0
    for s in signals:
        trend_multiplier = {
            KeywordSearchVolumeTrend.RISING: 1.0,
            KeywordSearchVolumeTrend.STEADY: 0.55,
            KeywordSearchVolumeTrend.DECLINING: 0.10,
            KeywordSearchVolumeTrend.UNKNOWN: 0.30,
        }.get(s.volume_trend, 0.30)
        # Volume normalization · 10k+/mo treated as saturated max
        vol = s.monthly_search_volume or 0
        vol_norm = min(vol / 10_000.0, 1.0)
        component = vol_norm * trend_multiplier
        if component > best:
            best = component
    return min(best, 1.0)


def _score_social_trend(signals: list[SocialTrendSignal]) -> float:
    """Highest momentum_score across signals · clamped to [0,1]."""
    if not signals:
        return 0.0
    best = 0.0
    for s in signals:
        if s.momentum_score is not None and s.momentum_score > best:
            best = s.momentum_score
    return min(max(best, 0.0), 1.0)


def _score_marketplace_sold(researches: list[MarketplaceSalesResearch]) -> float:
    """Higher when there is analyst-reviewed sold-price + units estimate."""
    if not researches:
        return 0.0
    best = 0.0
    for r in researches:
        if r.analyst_review_status != "ANALYST_REVIEWED":
            continue
        if r.average_sold_price_usd is None:
            continue
        units = r.units_sold_estimate or 0
        units_norm = min(units / 500.0, 1.0)
        # If the price band is wide relative to average, discount
        # because volatility weakens the signal.
        if r.sold_price_band_min_usd and r.sold_price_band_max_usd and r.average_sold_price_usd:
            spread = (
                float(r.sold_price_band_max_usd - r.sold_price_band_min_usd)
                / float(r.average_sold_price_usd)
            )
            spread_penalty = max(0.0, 1.0 - min(spread, 1.0))
        else:
            spread_penalty = 0.6
        component = units_norm * spread_penalty
        if component > best:
            best = component
    return min(best, 1.0)


def _score_competitive_saturation_inverted(
    stores: list[StoreIntelligenceObservation],
) -> tuple[float, CompetitionLevel]:
    """Higher score when fewer dominant competitors · returns also the level."""
    if not stores:
        return 0.5, CompetitionLevel.UNKNOWN
    high_revenue = sum(1 for s in stores if (s.estimated_monthly_revenue_band or "").startswith("HIGH"))
    if high_revenue >= 8:
        return 0.0, CompetitionLevel.OVERSATURATED
    if high_revenue >= 4:
        return 0.25, CompetitionLevel.HIGH
    if high_revenue >= 2:
        return 0.55, CompetitionLevel.MEDIUM
    return 0.85, CompetitionLevel.LOW


def _score_gross_margin(scenarios: list[MarginScenario]) -> float:
    """Best-case gross margin %, clamped to [0,1] with 50% = full credit."""
    if not scenarios:
        return 0.0
    best_pct = 0.0
    for s in scenarios:
        if s.gross_margin_pct is not None and s.gross_margin_pct > best_pct:
            best_pct = s.gross_margin_pct
    # 50% gross margin → 1.0 · linear below, capped above
    return min(best_pct / 50.0, 1.0)


def _score_shipping_returns_inverted(scenarios: list[MarginScenario]) -> float:
    """Higher when shipping cost is low AND return rate estimate is low."""
    if not scenarios:
        return 0.5
    best = 0.0
    for s in scenarios:
        if s.target_retail_price_usd is None:
            continue
        shipping = float(s.shipping_cost_usd or 0)
        ship_pct = shipping / float(s.target_retail_price_usd) if s.target_retail_price_usd else 1.0
        ship_score = max(0.0, 1.0 - min(ship_pct / 0.25, 1.0))  # >25% = 0
        ret_pct = s.return_rate_estimate_pct or 5.0
        ret_score = max(0.0, 1.0 - min(ret_pct / 25.0, 1.0))    # 25% returns = 0
        component = 0.6 * ship_score + 0.4 * ret_score
        if component > best:
            best = component
    return min(best, 1.0)


def _score_brand_creative_fit(opportunity: ProductOpportunity) -> float:
    """Subjective brandability hint · for v1 we use a coarse category bias.

    Future versions can incorporate human review / image-generation
    feasibility scoring.
    """
    from app.models.productradar import ProductCategory
    brand_fit = {
        ProductCategory.HOME_ORGANIZATION: 0.85,
        ProductCategory.PET_ACCESSORIES: 0.85,
        ProductCategory.KITCHEN_LIFESTYLE: 0.80,
        ProductCategory.TRAVEL_ORGANIZATION: 0.75,
        ProductCategory.OUTDOOR_RECREATION: 0.80,
        ProductCategory.HOME_OFFICE: 0.70,
        ProductCategory.NON_MEDICAL_WELLNESS: 0.70,
        ProductCategory.SPECIALTY_STORAGE: 0.65,
        ProductCategory.OTHER: 0.50,
    }
    return brand_fit.get(opportunity.category, 0.50)


def _policy_risk_flag(opportunity: ProductOpportunity) -> PolicyRiskFlag:
    """v1 · category-based heuristic. Future: connector-driven check."""
    # Hook for future · category-by-category overrides go here.
    return PolicyRiskFlag.NONE


def _score_policy_risk_inverted(flag: PolicyRiskFlag) -> float:
    """Higher score when policy risk is low. REJECTED → 0."""
    return {
        PolicyRiskFlag.NONE: 1.0,
        PolicyRiskFlag.PLATFORM_RESTRICTED: 0.4,
        PolicyRiskFlag.SHIPPING_RESTRICTED: 0.5,
        PolicyRiskFlag.TRADEMARK_RISK: 0.3,
        PolicyRiskFlag.REGULATED_GOOD: 0.2,
        PolicyRiskFlag.REJECTED: 0.0,
    }.get(flag, 0.5)


# ────────────────────────────────────────────────────────────────────
#  The scorer · deterministic + receipted
# ────────────────────────────────────────────────────────────────────


@dataclass
class OpportunityScore:
    total: float
    component_breakdown: dict
    competition_level: CompetitionLevel
    policy_risk_flag: PolicyRiskFlag
    signals_used_count: int
    confirmed_sale_signals_count: int
    recommendation: OpportunityRecommendation


def _gather_signals(db: Session, opportunity: ProductOpportunity) -> dict:
    """Pull every attached signal · returns a dict for the scorer."""
    return {
        "keywords": db.query(KeywordDemandSignal)
            .filter(KeywordDemandSignal.opportunity_id == opportunity.id).all(),
        "shopping": db.query(ShoppingPopularitySignal)
            .filter(ShoppingPopularitySignal.opportunity_id == opportunity.id).all(),
        "social": db.query(SocialTrendSignal)
            .filter(SocialTrendSignal.opportunity_id == opportunity.id).all(),
        "stores": db.query(StoreIntelligenceObservation)
            .filter(StoreIntelligenceObservation.opportunity_id == opportunity.id).all(),
        "research": db.query(MarketplaceSalesResearch)
            .filter(MarketplaceSalesResearch.opportunity_id == opportunity.id).all(),
        "suppliers": db.query(SupplierCandidate)
            .filter(SupplierCandidate.opportunity_id == opportunity.id).all(),
        "margins": db.query(MarginScenario)
            .filter(MarginScenario.opportunity_id == opportunity.id).all(),
        "store_outcomes": db.query(ConnectedStoreOutcome)
            .filter(ConnectedStoreOutcome.opportunity_id == opportunity.id).all(),
    }


def compute_score(db: Session, opportunity: ProductOpportunity) -> OpportunityScore:
    s = _gather_signals(db, opportunity)
    sd = _score_search_demand(s["keywords"])
    st = _score_social_trend(s["social"])
    ms = _score_marketplace_sold(s["research"])
    cs, comp_level = _score_competitive_saturation_inverted(s["stores"])
    gm = _score_gross_margin(s["margins"])
    sr = _score_shipping_returns_inverted(s["margins"])
    bf = _score_brand_creative_fit(opportunity)
    risk_flag = _policy_risk_flag(opportunity)
    pr = _score_policy_risk_inverted(risk_flag)

    breakdown = {
        "search_demand_growth": sd,
        "social_trend_velocity": st,
        "marketplace_sold_signal": ms,
        "competitive_saturation_inverted": cs,
        "gross_margin_feasibility": gm,
        "shipping_returns_risk_inverted": sr,
        "brand_creative_fit": bf,
        "policy_compliance_risk_inverted": pr,
    }

    total = (
        WEIGHTS["search_demand_growth"] * sd
        + WEIGHTS["social_trend_velocity"] * st
        + WEIGHTS["marketplace_sold_signal"] * ms
        + WEIGHTS["competitive_saturation"] * cs
        + WEIGHTS["gross_margin_feasibility"] * gm
        + WEIGHTS["shipping_returns_risk"] * sr
        + WEIGHTS["brand_creative_fit"] * bf
        + WEIGHTS["policy_compliance_risk"] * pr
    )

    signals_used = (
        len(s["keywords"]) + len(s["shopping"]) + len(s["social"])
        + len(s["stores"]) + len(s["research"]) + len(s["store_outcomes"])
    )
    confirmed_count = sum(
        1 for o in s["store_outcomes"]
        if o.signal_class in CONFIRMED_SALE_SIGNAL_CLASSES
    )

    # Recommendation rules · doctrine-enforced
    if risk_flag == PolicyRiskFlag.REJECTED:
        rec = OpportunityRecommendation.REJECT
    elif comp_level == CompetitionLevel.OVERSATURATED:
        rec = OpportunityRecommendation.REJECT
    elif total >= 0.70 and confirmed_count >= 1:
        rec = OpportunityRecommendation.LAUNCH_READY
    elif total >= 0.55 and any(sup.feasibility == SupplierFeasibility.FEASIBLE for sup in s["suppliers"]):
        rec = OpportunityRecommendation.PROCEED_TO_SUPPLIER_REVIEW
    elif total >= 0.35:
        rec = OpportunityRecommendation.GATHER_MORE_SIGNALS
    else:
        rec = OpportunityRecommendation.DEPRIORITIZE

    return OpportunityScore(
        total=round(total, 4),
        component_breakdown=breakdown,
        competition_level=comp_level,
        policy_risk_flag=risk_flag,
        signals_used_count=signals_used,
        confirmed_sale_signals_count=confirmed_count,
        recommendation=rec,
    )


def write_score_receipt(
    db: Session,
    opportunity: ProductOpportunity,
    score: OpportunityScore,
    notes: str | None = None,
) -> OpportunityScoreReceipt:
    """Persist a deterministic, SHA-256-hashed receipt."""
    receipt_payload = {
        "scoring_version": SCORING_VERSION,
        "opportunity_id": opportunity.opportunity_id,
        "total_score": score.total,
        "component_breakdown": score.component_breakdown,
        "competition_level": score.competition_level.value,
        "policy_risk_flag": score.policy_risk_flag.value,
        "signals_used_count": score.signals_used_count,
        "confirmed_sale_signals_count": score.confirmed_sale_signals_count,
        "recommendation": score.recommendation.value,
        "weights": WEIGHTS,
    }
    receipt_bytes = json.dumps(receipt_payload, sort_keys=True).encode("utf-8")
    receipt_sha256 = hashlib.sha256(receipt_bytes).hexdigest()

    receipt = OpportunityScoreReceipt(
        id=uuid.uuid4(),
        opportunity_id=opportunity.id,
        scoring_version=SCORING_VERSION,
        total_score=score.total,
        component_breakdown_json=score.component_breakdown,
        competition_level=score.competition_level,
        policy_risk_flag=score.policy_risk_flag,
        signals_used_count=score.signals_used_count,
        confirmed_sale_signals_count=score.confirmed_sale_signals_count,
        recommendation=score.recommendation,
        receipt_sha256=receipt_sha256,
        notes=notes,
    )
    db.add(receipt)

    # Denormalize onto the opportunity row for fast list display
    opportunity.latest_score = score.total
    opportunity.latest_score_at = datetime.now(tz=timezone.utc)
    opportunity.recommendation = score.recommendation

    db.flush()
    return receipt


# ────────────────────────────────────────────────────────────────────
#  Doctrine-enforced helpers · refuse confirmed-sale overclaims
# ────────────────────────────────────────────────────────────────────


def assert_launch_ready_safe(score: OpportunityScore) -> None:
    """Refuse to ship a LAUNCH_READY recommendation without at least one
    confirmed-sale signal · the only signal classes that count are
    PERMISSIONED_CONNECTED_SALE and FIRST_PARTY_DEFENDABLE_SALE.
    """
    if (
        score.recommendation == OpportunityRecommendation.LAUNCH_READY
        and score.confirmed_sale_signals_count == 0
    ):
        raise ProductRadarError(
            "LAUNCH_READY recommendation requires at least one "
            "PERMISSIONED_CONNECTED_SALE or FIRST_PARTY_DEFENDABLE_SALE "
            "signal · refusing to ship the recommendation"
        )


def assert_no_confirmed_sale_aggregation(signal_classes: list[SignalClass]) -> None:
    """Refuse to aggregate non-confirmed signals into a confirmed-sale
    claim in any output payload.
    """
    has_confirmed = any(c in CONFIRMED_SALE_SIGNAL_CLASSES for c in signal_classes)
    has_non_confirmed = any(c not in CONFIRMED_SALE_SIGNAL_CLASSES for c in signal_classes)
    if has_non_confirmed and not has_confirmed:
        raise ProductRadarError(
            "Aggregated signal set contains no PERMISSIONED_CONNECTED_SALE or "
            "FIRST_PARTY_DEFENDABLE_SALE · refuse to derive a confirmed-sale claim"
        )


# ────────────────────────────────────────────────────────────────────
#  Brand Outlet guards · BRANDED_COMMERCE_PLACEMENT doctrine
# ────────────────────────────────────────────────────────────────────


def assert_brand_placement_signal_safe(
    sales_confirmed: bool,
    supplier_authorization_confirmed: bool,
    signal_class: SignalClass,
) -> None:
    """Brand Outlet placement is NEVER a sales confirmation and NEVER
    a supplier authorization. The service refuses to ingest a row that
    sets either to True while claiming BRANDED_COMMERCE_PLACEMENT
    classification.
    """
    if signal_class != SignalClass.BRANDED_COMMERCE_PLACEMENT:
        return  # rule applies only to this class
    if sales_confirmed:
        raise ProductRadarError(
            "BRANDED_COMMERCE_PLACEMENT signals MUST have sales_confirmed=False · "
            "Brand Outlet placement is merchandising context, not sold proof"
        )
    if supplier_authorization_confirmed:
        raise ProductRadarError(
            "BRANDED_COMMERCE_PLACEMENT signals MUST have supplier_authorization_confirmed=False · "
            "appearing in Brand Outlet does not authorize us to resell the brand"
        )
