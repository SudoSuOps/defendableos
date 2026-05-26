"""Claw Agent Swarm · public endpoints for the live /defend-the-claw page.

POST /agent-swarm/clawcheck/intake   · one conversation turn (stateless · client carries findings)
GET  /agent-swarm/healthcheck        · team status + per-agent readiness
GET  /agent-swarm/roles              · full role manifest (Intake live · others scaffolded)
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.services.claw_swarm.intake_agent import (
    IntakeTurnRequest,
    run_intake_turn,
)
from app.services.claw_swarm.roles import roles_summary
from app.services.claw_bakery.ingest import ingest_intake_turn, ingest_snapshot
from app.core.config import settings


router = APIRouter(prefix="/agent-swarm", tags=["claw-swarm"])


class ConsentIn(BaseModel):
    store_for_snapshot: bool = True
    allow_deidentified_training_use: bool = False
    allow_evaluation_use: bool = False


class IntakeTurnIn(BaseModel):
    user_message: str = Field(..., min_length=1, max_length=4000)
    prior_findings: dict[str, Any] = Field(default_factory=dict)
    session_id: str | None = Field(default=None, max_length=128)
    consent: ConsentIn | None = None


class IntakeTurnOut(BaseModel):
    session_id: str | None
    agent_message: str
    findings: dict[str, Any]
    intake_complete: bool
    refusal_reason: str | None
    snapshot: dict[str, Any] | None
    judge_provider: dict[str, Any]
    raw_status: str
    doctrine_disclaimer: str
    bakery: dict[str, Any] | None = None


_DISCLAIMER = (
    "Claw Swarm · Intake Agent · Defendable disciplined evidence intake. "
    "Risk Tier is computed by platform code from documented rules · NOT by the model. "
    "This conversation does not call external systems · does not access your files · "
    "does not issue valuations or certifications · refuses anything outside Intake scope. "
    "See docs/DEFENDABLE_AGENT_GRADE.md and docs/TRIBUNAL_GRADING_DOCTRINE.md."
)


@router.post("/clawcheck/intake", response_model=IntakeTurnOut)
def clawcheck_intake(payload: IntakeTurnIn) -> IntakeTurnOut:
    req = IntakeTurnRequest(
        user_message=payload.user_message,
        prior_findings=payload.prior_findings,
    )
    res = run_intake_turn(req)

    # Bakery ingestion (best-effort · MUST NOT break the user response)
    consent = payload.consent.model_dump() if payload.consent else None
    bakery_envelope: dict[str, Any] | None = None
    intake_env = ingest_intake_turn(
        user_message=payload.user_message,
        findings=res.findings,
        intake_complete=res.intake_complete,
        refusal_reason=res.refusal_reason,
        judge_provider=res.judge_provider,
        consent=consent,
    )
    if intake_env is not None:
        bakery_envelope = {"intake": intake_env}
        if res.intake_complete and res.snapshot is not None:
            snap_env = ingest_snapshot(
                run_id=intake_env["run_id"],
                snapshot=res.snapshot,
                consent=consent,
            )
            if snap_env is not None:
                bakery_envelope["snapshot"] = snap_env

    return IntakeTurnOut(
        session_id=payload.session_id,
        agent_message=res.agent_message,
        findings=res.findings,
        intake_complete=res.intake_complete,
        refusal_reason=res.refusal_reason,
        snapshot=res.snapshot,
        judge_provider=res.judge_provider,
        raw_status=res.raw_status,
        doctrine_disclaimer=_DISCLAIMER,
        bakery=bakery_envelope,
    )


@router.get("/healthcheck")
def healthcheck() -> dict[str, Any]:
    return {
        "service": "claw-swarm",
        # Codex exposure repair: provider-configured booleans + model name removed from the
        # public probe. Detailed readiness (provider/model) lives behind the admin gate.
        "intake": "available",
        "team": roles_summary(),
        "doctrine_disclaimer": _DISCLAIMER,
    }


@router.get("/roles")
def roles() -> dict[str, Any]:
    return roles_summary()
