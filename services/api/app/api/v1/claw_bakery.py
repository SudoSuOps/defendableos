"""Claw Bakery · public + admin endpoints.

Public:
  GET  /claw-bakery/healthcheck       · driver / dir-tree / ClawForge status
  GET  /claw-bakery/public-metrics    · aggregate-only counts safe to render
  GET  /claw-bakery/seeded-fixtures   · SwarmScout · RefundRanger · RootClaw

Admin (placeholder · 501 until auth wire-up):
  GET  /claw-bakery/admin/pair-candidates
  POST /claw-bakery/admin/pair-candidates/{pair_id}/tribunal
  POST /claw-bakery/admin/clawforge/generate
  GET  /claw-bakery/admin/events

The admin layer requires the existing JWT admin pattern. v1 of this
file documents the routes and returns 501 NotImplemented until the
auth wire-up lands · we will not expose private bakery records over
an unauthenticated route.
"""
from __future__ import annotations

from typing import Any, Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.claw_bakery.bakery_storage import (
    BAKERY_DIRS,
    get_bakery_store,
)
from app.services.claw_bakery.clawforge import (
    is_enabled as clawforge_enabled,
    status_summary as clawforge_status_summary,
)
from app.services.claw_bakery.ingest import safe_public_metrics
from app.services.claw_swarm import fixtures
from app.services.claw_swarm.risk import evaluate_intake
from app.services.claw_swarm.structured_intake import derive_structured_intake


router = APIRouter(prefix="/claw-bakery", tags=["claw-bakery"])


# ─── Public ──────────────────────────────────────────────────────────


@router.get("/healthcheck")
def bakery_healthcheck() -> dict[str, Any]:
    store = get_bakery_store()
    forge = clawforge_status_summary(store)
    return {
        "service": "claw-bakery",
        "driver": store.driver.name,
        "bakery_dirs": list(BAKERY_DIRS),
        "clawforge": {
            "enabled": forge.enabled,
            "generated_total": forge.generated_total,
            "pending": forge.pending,
            "honey": forge.honey,
            "jelly_repaired": forge.jelly_repaired,
            "propolis": forge.propolis,
            "sealed_holdouts": forge.sealed_holdouts,
        },
        "doctrine": {
            "real_time_ingestion": "allowed",
            "real_time_candidate_pair_creation": "allowed",
            "real_time_hash_receipts": "allowed",
            "synthetic_case_generation": "allowed_in_controlled_queue",
            "automatic_positive_labeling": "prohibited",
            "automatic_training_on_raw_records": "prohibited",
            "tribunal_required_before_training_admission": True,
            "validator_required_before_deed_eligibility": True,
            "raw_evidence_is_immutable": True,
            "training_requires_redaction_and_consent": True,
            "holdout_contamination": "prohibited",
        },
    }


@router.get("/public-metrics")
def public_metrics() -> dict[str, Any]:
    """Aggregate-only counts safe to render on /claw-bakery. NEVER
    exposes raw user records, agent names, or operator_attested_context.
    """
    return safe_public_metrics()


@router.get("/seeded-fixtures")
def seeded_fixtures() -> dict[str, Any]:
    """Return SwarmScout / RefundRanger / RootClaw demo fixtures with
    computed rule_ids. Used by the public /claw-bakery seeded-lanes
    section. No private user data.
    """
    out: dict[str, dict[str, Any]] = {}
    for key, fx in fixtures.ALL_FIXTURES.items():
        si = derive_structured_intake(
            agent_name=fx["agent_name"],
            worker_kind=fx["worker_kind"],
            deployment_target=fx["deployment_target"],
            model_provider=fx["model_provider"],
            memory_enabled=fx["memory_enabled"],
            access_surfaces=fx["access_surfaces"],
            operator_attested_context=fx["operator_attested_context"],
        )
        risk = evaluate_intake(si)
        out[key] = {
            "agent_name": fx["agent_name"],
            "worker_kind": fx["worker_kind"],
            "deployment_target": fx["deployment_target"],
            "tier": risk["tier"],
            "rule_id": risk["rule_id"],
            "risk_class": risk.get("risk_class"),
            "deployment_status": risk["deployment_status"],
            "deed_eligibility": risk["deed_eligibility"],
            "future_deed_path": risk.get("future_deed_path"),
            "reason": risk["reason"],
            "evidence_cited": risk["evidence_cited"],
            "recommended_path": risk["recommended_path"],
            "doctrine_note": (
                "Seeded demonstration fixture · not a real customer record. "
                "Risk derived from explicit access_surfaces + grounded "
                "keyword detection over operator_attested_context. No agent "
                "approves its own tier."
            ),
        }
    return {"fixtures": out, "fixture_count": len(out)}


# ─── Admin (placeholders · auth required before live) ────────────────


class TribunalAssignIn(BaseModel):
    label: Literal["HONEY", "JELLY", "JELLY_REPAIRED_TO_HONEY", "PROPOLIS", "QUARANTINED"]
    reason: str


@router.get("/admin/pair-candidates")
def admin_list_pair_candidates() -> dict[str, Any]:
    raise HTTPException(
        status_code=501,
        detail=(
            "Admin pair-candidate listing requires JWT admin auth wire-up. "
            "The bakery storage layer is ready · the route stub is reserved. "
            "Until the auth gate is wired, private bakery records remain "
            "unreachable from any public route by design."
        ),
    )


@router.post("/admin/pair-candidates/{pair_id}/tribunal")
def admin_assign_tribunal_label(pair_id: str, payload: TribunalAssignIn) -> dict[str, Any]:
    raise HTTPException(
        status_code=501,
        detail=(
            "Tribunal label assignment requires admin auth + a 2-person review "
            "doctrine. Route reserved · backend logic in services/claw_bakery/"
            "pair_factory.assign_tribunal_label is ready."
        ),
    )


@router.post("/admin/clawforge/generate")
def admin_clawforge_generate() -> dict[str, Any]:
    if not clawforge_enabled():
        raise HTTPException(
            status_code=409,
            detail=(
                "ClawForge is disabled. Set CLAW_BAKERY_CLAWFORGE_ENABLED=true "
                "to enable controlled synthetic-case generation. Generated "
                "candidates ALWAYS land in pair-candidates/pending/ with "
                "synthetic=true and tribunal_label=PENDING."
            ),
        )
    raise HTTPException(
        status_code=501,
        detail=(
            "ClawForge generation endpoint requires admin auth. Backend logic "
            "in services/claw_bakery/clawforge.generate_synthetic_candidate is "
            "ready · the route stub is reserved."
        ),
    )


@router.get("/admin/events")
def admin_events() -> dict[str, Any]:
    raise HTTPException(
        status_code=501,
        detail=(
            "Event listing requires admin auth. The bakery_events outbox is "
            "live · events are written as immutable JSON under claw-bakery/"
            "events/ · admin route reserved."
        ),
    )
