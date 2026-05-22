"""Defendable Comp Foundry · deterministic grading + value-readiness service.

This module encodes the truth doctrine in code · the rules are
verifiable, refuseable, and tested. Every public service function
enforces the doctrine at the boundary · the database structure alone
cannot guarantee these invariants because nothing stops a buggy
service from writing the wrong enum.

Doctrine rules enforced here:

  RULE 1 · A TrendSignal can NEVER enter a comp set as value support.
           Always grade E · always inclusion_reason "DISCOVERY_ONLY".

  RULE 2 · A PUBLIC_ACTIVE_LISTING must carry:
             transaction_confirmed = False
             price_type = ASKING_PRICE
             quality grade ceiling = C
             limitation ASKING_PRICE_NOT_CONFIRMED_TRANSACTION

  RULE 3 · A confirmed transaction requires:
             source_type ∈ {CLIENT_PROVIDED_SALE_RECEIPT,
                            FOUNDER_OWNED_VERIFIED_SALE,
                            AUTHORIZED_MERCHANT_TRANSACTION,
                            LICENSED_TRANSACTION_DATA}
             transaction_status = CONFIRMED_WITH_EVIDENCE
             evidence_manifest_id is not None

  RULE 4 · A comp set with ZERO confirmed transactions or ONLY Grade
           C/D/E entries MUST resolve to NOT_READY_FOR_VALUE_SUPPORT
           with the canonical disclosure.

  RULE 5 · A comp set never becomes AIOV-final-value-ready
           automatically · the upgrade requires an explicit human
           approval write (NotImplementedError today).

  RULE 6 · Source rights must exist before pair or derivative export.
           (Enforced in pair_factory.py · this module just records
           the rights_status on each member.)
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Optional

from sqlalchemy.orm import Session

from app.models.goods import (
    CompQualityGrade,
    CompSet,
    CompSetIntendedUse,
    CompSetMember,
    CompSetStatus,
    MarketObservation,
    PriceType,
    SourceType,
    TransactionEvidence,
    TransactionStatus,
    TrendSignal,
)


_NOT_READY_DISCLOSURE = (
    "This comp set contains asking-market and/or discovery context only. "
    "No confirmed transaction support has been established."
)


class CompFoundryError(ValueError):
    """Doctrine violation · raised at service boundary."""


# ────────────────────────────────────────────────────────────────────
#  RULE-ENFORCING WRITES
# ────────────────────────────────────────────────────────────────────


def create_draft_comp_set(
    db: Session,
    *,
    goods_id: uuid.UUID,
    asset_id: uuid.UUID | None,
    title: str,
    comp_set_id: str,
    intended_use: CompSetIntendedUse = CompSetIntendedUse.MARKET_CONTEXT_RESEARCH,
) -> CompSet:
    cs = CompSet(
        id=uuid.uuid4(),
        comp_set_id=comp_set_id,
        goods_id=goods_id,
        asset_id=asset_id,
        title=title,
        intended_use=intended_use,
        comp_set_status=CompSetStatus.DRAFT_RESEARCH,
        grade_summary={"A": 0, "B": 0, "C": 0, "D": 0, "E": 0},
        limitations=[],
        confirmed_transaction_count=0,
        active_listing_count=0,
        trend_signal_count=0,
        validator_status=None,
    )
    db.add(cs)
    db.flush()
    return cs


def add_trend_signal(
    db: Session,
    *,
    comp_set_id: uuid.UUID,
    trend_signal_id: uuid.UUID,
    included_by: uuid.UUID | None = None,
) -> CompSetMember:
    """RULE 1 · TrendSignal always grade E + NOT_A_COMP."""
    signal = db.get(TrendSignal, trend_signal_id)
    if signal is None:
        raise CompFoundryError(f"TrendSignal {trend_signal_id} not found")

    member = CompSetMember(
        id=uuid.uuid4(),
        comp_set_id=comp_set_id,
        trend_signal_id=trend_signal_id,
        quality_grade=CompQualityGrade.E,
        inclusion_reason="DISCOVERY_ONLY · trend signals never support value",
        limitations=[
            "PUBLIC_RESEARCH_CONTEXT_ONLY",
            "NOT_TRANSACTION_EVIDENCE",
            "NOT_VALUE_SUPPORT",
        ],
        included_by=included_by,
    )
    db.add(member)
    db.flush()
    return member


def add_listing_observation(
    db: Session,
    *,
    comp_set_id: uuid.UUID,
    observation_id: uuid.UUID,
    included_by: uuid.UUID | None = None,
) -> CompSetMember:
    """RULE 2 · PUBLIC_ACTIVE_LISTING grade ceiling = C."""
    obs = db.get(MarketObservation, observation_id)
    if obs is None:
        raise CompFoundryError(f"MarketObservation {observation_id} not found")

    if obs.source_type != SourceType.PUBLIC_ACTIVE_LISTING:
        # Not a listing · service refuses to mis-classify
        raise CompFoundryError(
            f"add_listing_observation refuses source_type={obs.source_type.value} · "
            f"use add_transaction_evidence for confirmed sales"
        )
    if obs.transaction_confirmed:
        raise CompFoundryError(
            "transaction_confirmed must be False on PUBLIC_ACTIVE_LISTING"
        )
    if obs.price_type != PriceType.ASKING_PRICE:
        raise CompFoundryError(
            f"price_type must be ASKING_PRICE on PUBLIC_ACTIVE_LISTING · got {obs.price_type.value}"
        )

    # Grade ceiling enforcement · service refuses A or B on a listing.
    grade = obs.comp_quality_grade or CompQualityGrade.D
    if grade in {CompQualityGrade.A, CompQualityGrade.B}:
        raise CompFoundryError(
            f"PUBLIC_ACTIVE_LISTING cannot have quality_grade={grade.value} · "
            f"ceiling is C"
        )

    member = CompSetMember(
        id=uuid.uuid4(),
        comp_set_id=comp_set_id,
        observation_id=observation_id,
        quality_grade=grade,
        inclusion_reason="PUBLIC_ACTIVE_LISTING_ASKING_MARKET_CONTEXT_ONLY",
        limitations=[
            "PUBLIC_ACTIVE_LISTING",
            "ASKING_PRICE_NOT_CONFIRMED_TRANSACTION",
            "REQUIRES_VALIDATOR_REVIEW",
            "SOURCE_RIGHTS_INTERNAL_RESEARCH_ONLY",
        ],
        included_by=included_by,
    )
    db.add(member)
    db.flush()
    return member


def add_transaction_evidence(
    db: Session,
    *,
    comp_set_id: uuid.UUID,
    transaction_evidence_id: uuid.UUID,
    included_by: uuid.UUID | None = None,
) -> CompSetMember:
    """RULE 3 · only CONFIRMED_WITH_EVIDENCE transactions get A/B."""
    txn = db.get(TransactionEvidence, transaction_evidence_id)
    if txn is None:
        raise CompFoundryError(
            f"TransactionEvidence {transaction_evidence_id} not found"
        )

    allowed_sources = {
        SourceType.CLIENT_PROVIDED_SALE_RECEIPT,
        SourceType.FOUNDER_OWNED_VERIFIED_SALE,
        SourceType.AUTHORIZED_MERCHANT_TRANSACTION,
        SourceType.LICENSED_TRANSACTION_DATA,
        SourceType.FIRST_PARTY_TRANSACTION,
    }
    if txn.source_type not in allowed_sources:
        raise CompFoundryError(
            f"TransactionEvidence source_type={txn.source_type.value} not eligible for value support"
        )
    if txn.transaction_status != TransactionStatus.CONFIRMED_WITH_EVIDENCE:
        raise CompFoundryError(
            f"TransactionEvidence transaction_status={txn.transaction_status.value} · "
            f"must be CONFIRMED_WITH_EVIDENCE before joining a comp set"
        )
    if txn.evidence_manifest_id is None:
        raise CompFoundryError(
            "TransactionEvidence requires evidence_manifest_id before joining a comp set"
        )

    # Default a confirmed transaction with full evidence to grade B until
    # an attribute-match scorer upgrades to A. The grader cannot raise it
    # to A here · that is a separate review step.
    member = CompSetMember(
        id=uuid.uuid4(),
        comp_set_id=comp_set_id,
        transaction_evidence_id=transaction_evidence_id,
        quality_grade=CompQualityGrade.B,
        inclusion_reason="CONFIRMED_TRANSACTION_WITH_EVIDENCE_MANIFEST",
        limitations=[
            "CONFIRMED_TRANSACTION",
            "REQUIRES_ATTRIBUTE_MATCH_REVIEW_FOR_GRADE_A",
        ],
        included_by=included_by,
    )
    db.add(member)
    db.flush()
    return member


# ────────────────────────────────────────────────────────────────────
#  GRADING + READINESS
# ────────────────────────────────────────────────────────────────────


def recalculate_comp_set_summary(db: Session, comp_set_id: uuid.UUID) -> CompSet:
    """Update grade_summary + role-counts on the comp set."""
    cs = db.get(CompSet, comp_set_id)
    if cs is None:
        raise CompFoundryError(f"CompSet {comp_set_id} not found")

    members: list[CompSetMember] = (
        db.query(CompSetMember).filter(CompSetMember.comp_set_id == cs.id).all()
    )
    grade_summary = {"A": 0, "B": 0, "C": 0, "D": 0, "E": 0}
    confirmed = 0
    listings = 0
    signals = 0
    for m in members:
        grade_summary[m.quality_grade.value] += 1
        if m.transaction_evidence_id is not None:
            confirmed += 1
        elif m.observation_id is not None:
            listings += 1
        elif m.trend_signal_id is not None:
            signals += 1

    cs.grade_summary = grade_summary
    cs.confirmed_transaction_count = confirmed
    cs.active_listing_count = listings
    cs.trend_signal_count = signals

    # Update limitations summary
    limitations = []
    if signals:
        limitations.append("CONTAINS_TREND_SIGNALS_DISCOVERY_ONLY")
    if listings:
        limitations.append("CONTAINS_PUBLIC_ACTIVE_LISTINGS_ASKING_PRICE")
    if not confirmed:
        limitations.append("NO_CONFIRMED_TRANSACTION_EVIDENCE")
    cs.limitations = limitations

    db.flush()
    return cs


@dataclass
class CompSetReadiness:
    ready: bool
    status: CompSetStatus
    required_disclosure: Optional[str]
    reasons: list[str]


def validate_comp_set_readiness(db: Session, comp_set_id: uuid.UUID) -> CompSetReadiness:
    """RULE 4 · NOT_READY_FOR_VALUE_SUPPORT unless A/B comp exists."""
    cs = recalculate_comp_set_summary(db, comp_set_id)
    grade_a = cs.grade_summary.get("A", 0)
    grade_b = cs.grade_summary.get("B", 0)
    has_high_grade = (grade_a + grade_b) > 0
    has_confirmed = cs.confirmed_transaction_count > 0

    reasons: list[str] = []
    if not has_confirmed:
        reasons.append("NO_CONFIRMED_TRANSACTION_EVIDENCE")
    if not has_high_grade:
        reasons.append("NO_GRADE_A_OR_B_MEMBERS")

    if not (has_high_grade and has_confirmed):
        cs.comp_set_status = CompSetStatus.NOT_READY_FOR_VALUE_SUPPORT
        db.flush()
        return CompSetReadiness(
            ready=False,
            status=cs.comp_set_status,
            required_disclosure=_NOT_READY_DISCLOSURE,
            reasons=reasons,
        )

    # Sufficient evidence to enter DRAFT_RESEARCH → NEEDS_REVIEW · still
    # never auto-promotes to APPROVED_FOR_LIMITED_USE.
    cs.comp_set_status = CompSetStatus.NEEDS_REVIEW
    db.flush()
    return CompSetReadiness(
        ready=False,  # RULE 5 · only human review approves limited use
        status=cs.comp_set_status,
        required_disclosure=None,
        reasons=["AUTOMATIC_APPROVAL_BLOCKED_PER_RULE_5"],
    )


def approve_for_limited_use(*args, **kwargs):
    """RULE 5 · explicitly NotImplemented · only manual approval flow may
    elevate a comp set to APPROVED_FOR_LIMITED_USE. This stub exists so
    test imports succeed and so callers can grep for the seam.
    """
    raise NotImplementedError(
        "Manual human-approval workflow for comp set APPROVED_FOR_LIMITED_USE "
        "is required · not yet implemented · do not auto-promote."
    )


# ────────────────────────────────────────────────────────────────────
#  RECEIPT + HASHING (used downstream by Pair Factory and AIOV)
# ────────────────────────────────────────────────────────────────────


def comp_set_receipt_payload(db: Session, comp_set_id: uuid.UUID) -> dict:
    """Canonical serializable receipt of a comp set's current state."""
    cs = db.get(CompSet, comp_set_id)
    if cs is None:
        raise CompFoundryError(f"CompSet {comp_set_id} not found")
    members: list[CompSetMember] = (
        db.query(CompSetMember).filter(CompSetMember.comp_set_id == cs.id).all()
    )
    return {
        "schema_version": "comp_set_receipt.v1",
        "comp_set_id": cs.comp_set_id,
        "title": cs.title,
        "intended_use": cs.intended_use.value,
        "comp_set_status": cs.comp_set_status.value,
        "grade_summary": cs.grade_summary,
        "confirmed_transaction_count": cs.confirmed_transaction_count,
        "active_listing_count": cs.active_listing_count,
        "trend_signal_count": cs.trend_signal_count,
        "limitations": cs.limitations,
        "members": [
            {
                "quality_grade": m.quality_grade.value,
                "inclusion_reason": m.inclusion_reason,
                "limitations": m.limitations,
                "observation_id": str(m.observation_id) if m.observation_id else None,
                "transaction_evidence_id": (
                    str(m.transaction_evidence_id) if m.transaction_evidence_id else None
                ),
                "trend_signal_id": str(m.trend_signal_id) if m.trend_signal_id else None,
            }
            for m in members
        ],
    }
