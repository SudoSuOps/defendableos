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
from app.core.config import settings


router = APIRouter(prefix="/agent-swarm", tags=["claw-swarm"])


class IntakeTurnIn(BaseModel):
    user_message: str = Field(..., min_length=1, max_length=4000)
    prior_findings: dict[str, Any] = Field(default_factory=dict)
    session_id: str | None = Field(default=None, max_length=128)


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
    )


@router.get("/healthcheck")
def healthcheck() -> dict[str, Any]:
    return {
        "service": "claw-swarm",
        "kimi_configured": bool(settings.moonshot_api_key),
        "kimi_model": settings.moonshot_model if settings.moonshot_api_key else None,
        "intake_status": "LIVE" if settings.moonshot_api_key else "STUB_DETERMINISTIC_FALLBACK",
        "team": roles_summary(),
        "doctrine_disclaimer": _DISCLAIMER,
    }


@router.get("/roles")
def roles() -> dict[str, Any]:
    return roles_summary()
