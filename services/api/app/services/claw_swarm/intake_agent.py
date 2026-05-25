"""Intake Agent · the live ClawCheck conversational front door.

Routes every model call through the platform's model_gateway · so
MODEL_PROVIDER=kimi|swarmcurator|openai is honored uniformly. The
typed `record_intake_findings` tool contract is provider-agnostic.
Stateless per request · the client (landing page) accumulates findings
across turns.

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


def _gateway_intake_turn(req: IntakeTurnRequest) -> IntakeTurnResponse:
    """Real intake turn via the platform model_gateway (Kimi/SwarmCurator/OpenAI)."""
    from app.integrations.model_gateway import (
        ToolDefinition,
        get_model_gateway,
    )
    from app.models.ai import WorkflowType

    gateway = get_model_gateway()
    provider_name = gateway.provider.name
    provider_model = gateway.provider.model
    provider_meta = {
        "provider": provider_name,
        "model": provider_model,
        "configured": gateway.provider.is_configured(),
    }

    if not gateway.provider.is_configured():
        fallback = _stub_intake(req)
        fallback.judge_provider = provider_meta
        fallback.raw_status = f"NOT_CONFIGURED_{provider_name.upper()}"
        return fallback

    prior_context = json.dumps(req.prior_findings or {}, sort_keys=True, indent=2)[:1500]

    # The intake tool is provider-agnostic · model_gateway repackages it as
    # the provider's function-call spec.
    tool_def = ToolDefinition(
        name=CLAW_INTAKE_TOOL["function"]["name"],
        description=CLAW_INTAKE_TOOL["function"]["description"],
        parameters=CLAW_INTAKE_TOOL["function"]["parameters"],
    )

    prompt_payload = {
        "system_prompt": CLAW_INTAKE_SYSTEM_PROMPT,
        "user_message": req.user_message[:2000],
        "prior_findings": req.prior_findings or {},
        "instructions": (
            "Update findings with anything new the operator just told you, "
            "then propose the next message. Call the record_intake_findings tool. "
            "When all 5 dimensions are captured · set intake_complete=true."
        ),
        "prior_context_preview": prior_context,
    }

    try:
        result = gateway.generate_structured(
            workflow_type=WorkflowType.VALIDATOR_ASSIST,
            prompt_version="claw_intake_v1",
            input_reference={"session_id": req.session_id},
            prompt_payload=prompt_payload,
            thinking_enabled=False,
            tools=[tool_def],
        )
    except Exception as exc:  # noqa: BLE001
        fallback = _stub_intake(req)
        fallback.raw_status = f"FAILED_EXCEPTION_{type(exc).__name__}"
        fallback.judge_provider = provider_meta
        return fallback

    if result.status != "GENERATED":
        return IntakeTurnResponse(
            agent_message=(
                "The Intake agent could not reach the model · serving deterministic "
                "stub fallback. " + _stub_intake(req).agent_message
            ),
            findings=req.prior_findings,
            intake_complete=False,
            refusal_reason=None,
            snapshot=None,
            judge_provider=provider_meta,
            raw_status=f"FAILED_{result.status}",
        )

    if not result.tool_calls:
        return IntakeTurnResponse(
            agent_message=(result.output_text or "")[:1500]
            or "Intake response had no tool call · please retry.",
            findings=req.prior_findings,
            intake_complete=False,
            refusal_reason=None,
            snapshot=None,
            judge_provider=provider_meta,
            raw_status="NO_TOOL_CALL",
        )

    args = result.tool_calls[0].arguments or {}
    if not isinstance(args, dict):
        return IntakeTurnResponse(
            agent_message="Intake tool-call arguments did not parse · please retry.",
            findings=req.prior_findings,
            intake_complete=False,
            refusal_reason=None,
            snapshot=None,
            judge_provider=provider_meta,
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
        judge_provider=provider_meta,
        raw_status="RAN",
    )


# Legacy alias · kept until call sites stop referencing the old name.
_kimi_intake_turn = _gateway_intake_turn


def run_intake_turn(req: IntakeTurnRequest) -> IntakeTurnResponse:
    """Public entry point · falls back to deterministic stub when no provider configured."""
    from app.integrations.model_gateway import get_model_gateway

    if get_model_gateway().provider.is_configured():
        return _gateway_intake_turn(req)
    return _stub_intake(req)
