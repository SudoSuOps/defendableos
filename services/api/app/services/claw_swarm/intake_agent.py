"""Intake Agent · the live ClawCheck conversational front door.

Uses the platform's model_gateway · primary provider Kimi K2.6 ·
typed `record_intake_findings` tool contract. Stateless per request
· the client (landing page) accumulates findings across turns.

Doctrine guarantees:
  · Refuses any request outside Intake scope (price · action · file
    access · certification) via the refusal_reason channel
  · Risk Tier is NEVER computed by the model · only by code in risk.py
  · Snapshot only assembles when intake_complete=true AND all 5
    ClawCheck dimensions are present
  · Returns rule-only deterministic snapshot when no model is configured
    (graceful degradation · matches the /defend-the-claw page exactly)
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from app.core.config import settings
from app.services.claw_swarm.risk import (
    compute_risk_tier,
    evaluate_intake,
    recommended_product,
)
from app.services.claw_swarm.roles import CLAW_INTAKE_SYSTEM_PROMPT, CLAW_INTAKE_TOOL
from app.services.claw_swarm.structured_intake import derive_structured_intake


@dataclass
class IntakeTurnRequest:
    user_message: str
    prior_findings: dict[str, Any]


@dataclass
class IntakeTurnResponse:
    agent_message: str
    findings: dict[str, Any]
    intake_complete: bool
    refusal_reason: str | None
    snapshot: dict[str, Any] | None
    judge_provider: dict[str, Any]
    raw_status: str


def _merge_findings(prior: dict[str, Any], new: dict[str, Any]) -> dict[str, Any]:
    """Merge new findings into prior · arrays union · scalars overwrite."""
    out = dict(prior or {})
    for k, v in (new or {}).items():
        if v is None:
            continue
        if k == "access_surfaces" and isinstance(v, list):
            existing = set(out.get(k, []) or [])
            existing.update(v)
            out[k] = sorted(existing)
        else:
            out[k] = v
    return out


def _all_five_present(findings: dict[str, Any]) -> bool:
    required = ("worker_kind", "deployment_target", "access_surfaces", "model_provider")
    if not all(findings.get(k) for k in required):
        return False
    if not findings.get("access_surfaces"):
        return False
    # memory_enabled may be False (valid value) · must be explicit
    return findings.get("memory_enabled") is not None


def _assemble_snapshot(findings: dict[str, Any]) -> dict[str, Any]:
    # Evidence-specific rule evaluation · uses the structured-intake
    # projection so reasons match the actual permissions / sensitive
    # access detected. Falls back to the legacy heuristic only when no
    # specific rule matches.
    structured = derive_structured_intake(
        agent_name=findings.get("agent_name"),
        worker_kind=findings.get("worker_kind"),
        deployment_target=findings.get("deployment_target"),
        model_provider=findings.get("model_provider"),
        memory_enabled=findings.get("memory_enabled"),
        access_surfaces=findings.get("access_surfaces") or [],
        operator_attested_context=findings.get("operator_attested_context"),
    )
    risk = evaluate_intake(structured)
    legacy = compute_risk_tier(
        worker_kind=findings.get("worker_kind"),
        deployment_target=findings.get("deployment_target"),
        access_surfaces=findings.get("access_surfaces") or [],
        memory_enabled=findings.get("memory_enabled"),
    )
    rec = recommended_product(risk["tier"])
    return {
        "captured": findings,
        "structured_intake": structured.to_dict(),
        "risk": risk,
        "legacy_risk": legacy,
        "recommended": rec,
        "snapshot_kind": "CLAW_EXPOSURE_SNAPSHOT",
        "doctrine_note": (
            "Risk Tier is computed by platform code from documented rules · "
            "NOT by the model. The model's role is intake conversation only. "
            "Risk explanations are evidence-specific · they cite only the "
            "permission / sensitive-access flags actually detected."
        ),
    }


def _stub_intake(req: IntakeTurnRequest) -> IntakeTurnResponse:
    """Graceful degradation · runs when no MOONSHOT_API_KEY configured.

    The Intake agent becomes a deterministic state machine that mirrors
    the /defend-the-claw page · operators still get a complete Snapshot
    when they POST their findings, just without conversational reframing.
    """
    findings = req.prior_findings or {}
    if _all_five_present(findings):
        snap = _assemble_snapshot(findings)
        return IntakeTurnResponse(
            agent_message=(
                "Snapshot ready. Risk Tier computed from your selections by platform code. "
                "Recommended product: "
                + snap["recommended"]["product"]
            ),
            findings=findings,
            intake_complete=True,
            refusal_reason=None,
            snapshot=snap,
            judge_provider={"provider": "stub", "model": "deterministic-state-machine", "configured": False},
            raw_status="STUB_NO_MODEL",
        )
    missing = []
    if not findings.get("worker_kind"):
        missing.append("worker_kind")
    if not findings.get("deployment_target"):
        missing.append("deployment_target")
    if not findings.get("access_surfaces"):
        missing.append("access_surfaces")
    if not findings.get("model_provider"):
        missing.append("model_provider")
    if findings.get("memory_enabled") is None:
        missing.append("memory_enabled")
    return IntakeTurnResponse(
        agent_message=(
            "Intake running in stub mode (no model configured). "
            "Please submit selections for: " + ", ".join(missing)
        ),
        findings=findings,
        intake_complete=False,
        refusal_reason=None,
        snapshot=None,
        judge_provider={"provider": "stub", "model": "deterministic-state-machine", "configured": False},
        raw_status="STUB_NO_MODEL",
    )


def _kimi_intake_turn(req: IntakeTurnRequest) -> IntakeTurnResponse:
    """Real intake turn via Kimi K2.6."""
    import httpx

    api_key = settings.moonshot_api_key
    if not api_key:
        return _stub_intake(req)

    base_url = settings.moonshot_base_url
    model = settings.moonshot_model

    prior_context = json.dumps(req.prior_findings or {}, sort_keys=True, indent=2)[:1500]

    user_payload = (
        f"Operator message:\n{req.user_message[:2000]}\n\n"
        f"Prior intake findings (already collected):\n{prior_context}\n\n"
        "Update findings with anything new the operator just told you, "
        "then propose the next message. Call the record_intake_findings tool. "
        "When all 5 dimensions are captured · set intake_complete=true."
    )

    body = {
        "model": model,
        "temperature": 1,  # Kimi quirk · must be 1
        "messages": [
            {"role": "system", "content": CLAW_INTAKE_SYSTEM_PROMPT},
            {"role": "user", "content": user_payload},
        ],
        "tools": [CLAW_INTAKE_TOOL],
        "tool_choice": "auto",
    }
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    try:
        with httpx.Client(timeout=180.0) as client:
            r = client.post(f"{base_url}/chat/completions", headers=headers, json=body)
        if r.status_code >= 400:
            return IntakeTurnResponse(
                agent_message=(
                    "The Intake agent could not reach the model · serving deterministic "
                    "stub fallback. " + _stub_intake(req).agent_message
                ),
                findings=req.prior_findings,
                intake_complete=False,
                refusal_reason=None,
                snapshot=None,
                judge_provider={"provider": "kimi", "model": model, "configured": True},
                raw_status=f"FAILED_HTTP_{r.status_code}",
            )
        data = r.json()
    except Exception as exc:  # noqa: BLE001
        fallback = _stub_intake(req)
        fallback.raw_status = f"FAILED_EXCEPTION_{type(exc).__name__}"
        fallback.judge_provider = {"provider": "kimi", "model": model, "configured": True}
        return fallback

    choice = (data.get("choices") or [{}])[0]
    message = choice.get("message") or {}
    tool_calls = message.get("tool_calls") or []
    if not tool_calls:
        return IntakeTurnResponse(
            agent_message=(message.get("content") or "")[:1500]
            or "Intake response had no tool call · please retry.",
            findings=req.prior_findings,
            intake_complete=False,
            refusal_reason=None,
            snapshot=None,
            judge_provider={"provider": "kimi", "model": model, "configured": True},
            raw_status="NO_TOOL_CALL",
        )

    fn = tool_calls[0].get("function") or {}
    raw_args = fn.get("arguments") or "{}"
    try:
        args = json.loads(raw_args) if isinstance(raw_args, str) else (raw_args or {})
    except json.JSONDecodeError:
        return IntakeTurnResponse(
            agent_message="Intake tool-call arguments did not parse · please retry.",
            findings=req.prior_findings,
            intake_complete=False,
            refusal_reason=None,
            snapshot=None,
            judge_provider={"provider": "kimi", "model": model, "configured": True},
            raw_status="ARGS_PARSE_FAIL",
        )

    new_findings = args.get("findings") or {}
    merged = _merge_findings(req.prior_findings or {}, new_findings)
    next_msg = (args.get("next_message") or "")[:1500]
    intake_complete_claim = bool(args.get("intake_complete"))
    refusal = args.get("refusal_reason") or None

    # Code-side check · only treat as complete if ALL 5 dimensions are present
    code_complete = _all_five_present(merged)
    snapshot = _assemble_snapshot(merged) if code_complete else None

    return IntakeTurnResponse(
        agent_message=next_msg,
        findings=merged,
        intake_complete=code_complete and intake_complete_claim,
        refusal_reason=refusal,
        snapshot=snapshot,
        judge_provider={"provider": "kimi", "model": model, "configured": True},
        raw_status="RAN",
    )


def run_intake_turn(req: IntakeTurnRequest) -> IntakeTurnResponse:
    """Public entry point · falls back to deterministic stub when no key."""
    if settings.moonshot_api_key:
        return _kimi_intake_turn(req)
    return _stub_intake(req)
