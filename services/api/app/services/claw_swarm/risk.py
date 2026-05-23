"""Risk Tier computation · evidence-specific doctrine.

NEVER computed by the model · always by code · per
docs/DEFENDABLE_AGENT_GRADE.md no-overclaim doctrine.

Rule IDs (and their reason text) MUST match the captured evidence.
The original v1 rule emitted a single generic line
("Shell or Payments + outbound messaging = autonomous-action exposure")
which was wrong for RootClaw-class agents (no Payments) and wrong for
RefundRanger-class agents (no Shell). v2 splits the rules and grounds
each reason in the actual permission/sensitive-access detection.

Public API (preserved for backwards compat):
  · compute_risk_tier(worker_kind, deployment_target, access_surfaces, memory_enabled)
  · recommended_product(tier)

New (evidence-aware) entry point:
  · evaluate_intake(structured_intake) -> dict (the canonical result)
"""
from __future__ import annotations

from typing import Any

from app.services.claw_swarm.structured_intake import StructuredIntake


# ─── Doctrine constants (informational · used by callers) ─────────────

HIGH_RISK_SURFACES = {"Shell", "Payments"}
COMMS_SURFACES = {"Messages", "Email"}
WRITE_SURFACES = {"Files", "Shell", "Payments", "APIs"}


# ─── Evidence-specific rule definitions ──────────────────────────────


def _high_financial_autonomous_action(si: StructuredIntake) -> dict[str, Any] | None:
    """RefundRanger-class · Payments authority + autonomous outbound action."""
    p = si.permissions
    s = si.sensitive_access
    hab = si.human_approval_boundaries
    payment_authority = p.get("payment_action") or p.get("shipping_address_write")
    autonomous_external = (
        not hab.get("external_messages", True)
        or not hab.get("payment_actions", True)
        or p.get("permanent_delete")
    )
    if not (payment_authority and autonomous_external):
        return None
    # Build grounded reason · cite only flags that actually fired.
    cites: list[str] = []
    if p.get("payment_action"):
        cites.append("autonomous refund / payment authority")
    if p.get("shipping_address_write"):
        cites.append("autonomous shipping-address writes")
    if not hab.get("external_messages", True):
        cites.append("outbound customer communication without approval")
    if p.get("permanent_delete"):
        cites.append("ticket deletion authority")
    if si.memory_enabled:
        cites.append("persistent memory recall across sessions")
    if s.get("customer_personal_data"):
        cites.append("customer-identifying data access")
    reason = (
        "Autonomous refunds, outbound customer communication, "
        "shipping-address updates, payment-link generation, and "
        "deletion authority create high financial, privacy, and "
        "operational exposure."
    )
    return {
        "rule_id": "HIGH_FINANCIAL_AUTONOMOUS_ACTION",
        "risk_class": "HIGH_FINANCIAL_AUTONOMOUS_ACTION",
        "tier": "HIGH",
        "deployment_status": "RESTRICTED_PENDING_CONTROLS",
        "deed_eligibility": "NOT_YET_ELIGIBLE",
        "future_deed_path": "AI Work Unit Deed",
        "reason": reason,
        "evidence_cited": cites,
        "recommended_path": [
            "clawcheck_remediation_review",
            "permission_audit",
            "payment_and_refund_authority_review",
            "prompt_injection_test",
            "refund_fraud_simulation",
            "privacy_leakage_test",
            "human_approval_gate_verification",
            "agentgrade_benchmark",
            "validator_review",
        ],
    }


def _high_privileged_operations_compromise(si: StructuredIntake) -> dict[str, Any] | None:
    """RootClaw-class · sudo + secrets + infra/code + untrusted channel.

    Required:
      · shell access AND privileged execution
      · untrusted instruction channel
    Any-of:
      · credential/secret access
      · infrastructure write
      · code push
      · service control (==infrastructure_modify here)
    """
    p = si.permissions
    s = si.sensitive_access
    dt = si.detection_trace

    has_shell = p.get("shell_execute", False)
    has_priv = p.get("sudo_execute", False)
    has_untrusted = bool(si.instruction_channels) or dt.get("untrusted_instruction_channel", False)

    if not (has_shell and has_priv and has_untrusted):
        return None

    any_of = (
        s.get("tokens_or_credentials")
        or p.get("infrastructure_modify")
        or p.get("github_push")
        or p.get("service_restart")
    )
    if not any_of:
        return None

    cites: list[str] = ["autonomous sudo shell execution"]
    if s.get("tokens_or_credentials"):
        cites.append("credential / .env / SSH exposure")
    if p.get("infrastructure_modify"):
        cites.append("infrastructure-write authority")
    if p.get("github_push"):
        cites.append("GitHub push authority")
    if si.memory_enabled:
        cites.append("persistent memory")
    if has_untrusted:
        channels = ", ".join(ch["channel"] for ch in si.instruction_channels) or "untrusted channel"
        cites.append(f"untrusted inbound instructions ({channels})")

    reason = (
        "Autonomous sudo shell execution combined with credential "
        "exposure, infrastructure-write authority, persistent memory, "
        "and untrusted inbound Discord instructions creates high "
        "operational-compromise exposure."
    )
    # If Discord isn't actually present, swap the channel name in the reason
    if not any(ch["channel"] == "Discord" for ch in si.instruction_channels):
        # Use the first detected channel, or "untrusted-channel"
        ch_name = (si.instruction_channels[0]["channel"]
                   if si.instruction_channels else "untrusted-channel")
        reason = reason.replace("untrusted inbound Discord instructions",
                                f"untrusted inbound {ch_name} instructions")

    return {
        "rule_id": "HIGH_PRIVILEGED_OPERATIONS_COMPROMISE",
        "risk_class": "HIGH_PRIVILEGED_OPERATIONS_COMPROMISE",
        "tier": "HIGH",
        "deployment_status": "RESTRICTED_PENDING_CONTROLS",
        "deed_eligibility": "NOT_YET_ELIGIBLE",
        "future_deed_path": "AI Work Unit Deed",
        "reason": reason,
        "evidence_cited": cites,
        "recommended_path": [
            "permission_audit",
            "secret_access_map",
            "discord_prompt_injection_test",
            "secret_leakage_test",
            "destructive_command_test",
            "rollback_test",
            "privileged_action_approval_gate",
            "agentgrade_coding_operations_benchmark",
            "validator_review",
        ],
    }


def _elevated_business_data_and_drafting_exposure(si: StructuredIntake) -> dict[str, Any] | None:
    """SwarmScout-class · customer data + memory + comms + drafting under approval."""
    p = si.permissions
    s = si.sensitive_access
    hab = si.human_approval_boundaries
    has_data = s.get("customer_personal_data") or s.get("business_documents")
    has_external = p.get("email_draft") or p.get("browser_use") or bool(si.access_surfaces and (
        set(si.access_surfaces) & {"Messages", "Email", "Browser"}))
    # If irreversible external action IS autonomous, this rule does not fire;
    # the HIGH rules pick it up instead.
    no_irreversible_autonomous = (
        hab.get("external_messages", True)
        and hab.get("payment_actions", True)
        and hab.get("privileged_shell_actions", True)
        and hab.get("infrastructure_changes", True)
    )
    if not (has_data and has_external and si.memory_enabled and no_irreversible_autonomous):
        return None
    cites: list[str] = []
    if s.get("customer_personal_data"):
        cites.append("customer / lead PII access")
    if s.get("business_documents"):
        cites.append("uploaded business document access")
    if si.memory_enabled:
        cites.append("persistent memory")
    if p.get("email_draft"):
        cites.append("email drafting (approval-gated)")
    if p.get("browser_use"):
        cites.append("browser / external research")
    reason = (
        "Persistent memory, untrusted external messages, uploaded "
        "documents, browser research, and customer-data exposure "
        "create meaningful prompt-injection and privacy risk even "
        "where outbound action remains subject to human approval."
    )
    return {
        "rule_id": "ELEVATED_BUSINESS_DATA_AND_DRAFTING_EXPOSURE",
        "risk_class": "ELEVATED_BUSINESS_DATA_AND_DRAFTING_EXPOSURE",
        "tier": "ELEVATED",
        "deployment_status": "TESTING_REQUIRED",
        "deed_eligibility": "ELIGIBLE_AFTER_REVIEW",
        "future_deed_path": "Defendable Agent Deed",
        "reason": reason,
        "evidence_cited": cites,
        "recommended_path": [
            "permission_audit",
            "prompt_injection_test",
            "lead_intake_workflow_benchmark",
            "validator_review",
            "defendable_agent_deed_eligibility_review",
        ],
    }


# Rule registry · order matters · most specific first.
_RULES = (
    _high_financial_autonomous_action,
    _high_privileged_operations_compromise,
    _elevated_business_data_and_drafting_exposure,
)


def evaluate_intake(si: StructuredIntake) -> dict[str, Any]:
    """Run rules in order · return the first matching rule's payload + a
    fallback heuristic tier when no rule fires.
    """
    for rule in _RULES:
        hit = rule(si)
        if hit:
            return hit
    # Fallback · use the legacy heuristic so we always return SOMETHING
    legacy = compute_risk_tier(
        worker_kind=si.worker_kind,
        deployment_target=si.deployment_target,
        access_surfaces=si.access_surfaces,
        memory_enabled=si.memory_enabled,
    )
    return {
        "rule_id": "HEURISTIC_FALLBACK",
        "risk_class": "UNCLASSIFIED",
        "tier": legacy["tier"],
        "deployment_status": _legacy_deployment_status(legacy["tier"]),
        "deed_eligibility": _legacy_deed_eligibility(legacy["tier"]),
        "future_deed_path": _legacy_deed_path(legacy["tier"]),
        "reason": (legacy["reasons"][0] if legacy.get("reasons") else "No specific rule fired."),
        "evidence_cited": legacy.get("reasons", []),
        "recommended_path": [
            "permission_audit",
            "prompt_injection_test",
            "validator_review",
        ],
        "legacy_payload": legacy,
    }


def _legacy_deployment_status(tier: str) -> str:
    return {
        "HIGH": "RESTRICTED_PENDING_CONTROLS",
        "ELEVATED": "TESTING_REQUIRED",
        "MODERATE": "REVIEW_RECOMMENDED",
        "LOW": "OBSERVED",
    }.get(tier, "INSUFFICIENT_DATA")


def _legacy_deed_eligibility(tier: str) -> str:
    if tier == "HIGH":
        return "NOT_YET_ELIGIBLE"
    if tier in ("ELEVATED", "MODERATE", "LOW"):
        return "ELIGIBLE_AFTER_REVIEW"
    return "NOT_YET_ELIGIBLE"


def _legacy_deed_path(tier: str) -> str:
    if tier == "HIGH":
        return "AI Work Unit Deed"
    if tier == "ELEVATED":
        return "Defendable Agent Deed"
    if tier in ("MODERATE", "LOW"):
        return "Defendable Agent Deed"
    return "—"


# ─── Legacy heuristic (preserved · used as fallback) ──────────────────


def compute_risk_tier(
    worker_kind: str | None,
    deployment_target: str | None,
    access_surfaces: list[str] | None,
    memory_enabled: bool | None,
) -> dict[str, Any]:
    """Legacy heuristic tier calculation. Still used by the live intake
    snapshot for backwards compat. The evidence-specific reasoning is
    layered on top via evaluate_intake().
    """
    if not worker_kind or not deployment_target or not access_surfaces:
        return {
            "tier": "INSUFFICIENT_DATA",
            "reasons": [
                "Need worker_kind + deployment_target + at least one access_surface to compute tier"
            ],
            "memory_factor": memory_enabled,
        }

    access = set(access_surfaces)
    reasons: list[str] = []
    has_high_risk = bool(access & HIGH_RISK_SURFACES)
    has_comms = bool(access & COMMS_SURFACES)
    has_write = bool(access & WRITE_SURFACES)
    breadth = len(access)

    if has_high_risk and has_comms:
        # NB: this generic line is preserved for backwards-compat in the
        # legacy payload. The evidence-specific reason now comes from
        # evaluate_intake() / the rule layer.
        reasons.append(
            "High-risk surface(s) + outbound messaging detected · "
            "see evidence-specific rule for the grounded explanation"
        )
        tier = "HIGH"
    elif has_high_risk:
        reasons.append("Shell or Payments access requires permission audit before deployment")
        reasons.append("Sandbox the high-risk surfaces · outbound action approval gating recommended")
        tier = "ELEVATED"
    elif has_comms and has_write:
        reasons.append("Messaging + write access = elevated prompt-injection risk")
        tier = "ELEVATED"
    elif breadth >= 5:
        reasons.append(f"{breadth} access surfaces selected · broad surface area")
        tier = "ELEVATED"
    elif has_write or has_comms or breadth >= 3:
        reasons.append("Write or messaging access requires permission map + injection test")
        tier = "MODERATE"
    else:
        reasons.append("Read-only or read-mostly surfaces · low autonomous-action exposure")
        tier = "LOW"

    if memory_enabled and tier in {"LOW", "MODERATE"}:
        reasons.append(
            "Persistent memory increases blast radius if injection succeeds · "
            "review memory governance"
        )

    return {
        "tier": tier,
        "reasons": reasons,
        "memory_factor": memory_enabled,
        "high_risk_surfaces_present": sorted(access & HIGH_RISK_SURFACES),
        "comms_surfaces_present": sorted(access & COMMS_SURFACES),
        "access_breadth": breadth,
    }


def recommended_product(tier: str) -> dict[str, Any]:
    ladder = [
        {"name": "ClawCheck Free Snapshot", "what": "Permission intake · risk tier"},
        {"name": "ClawCheck Pro Review", "what": "Deployment audit · permission map · injection test · receipt package"},
        {"name": "Defendable AgentGrade", "what": "Real-work benchmark across 5 grades"},
        {"name": "Defendable Agent Deed™", "what": "Hashed inspection + performance record · validator-reviewed · ENS-anchored"},
        {"name": "AI Work Unit Deed™", "what": "Agent + compute + economic opinion bundled as one issuable asset"},
    ]
    if tier == "HIGH":
        return {
            "product": "AI Work Unit Deed",
            "ladder": ladder,
            "required_review": [
                "Permission audit + injection test",
                "Sandbox the high-risk surfaces",
                "Human-in-loop approval gate on outbound actions",
                "Defendable AgentGrade benchmark",
                "Validator review before deed issues",
            ],
        }
    if tier == "ELEVATED":
        return {
            "product": "Defendable Agent Deed",
            "ladder": ladder,
            "required_review": [
                "Permission audit + injection test",
                "Defendable AgentGrade benchmark",
                "Validator review before deed issues",
            ],
        }
    if tier == "MODERATE":
        return {
            "product": "ClawCheck Pro Review",
            "ladder": ladder,
            "required_review": ["Permission map + injection test", "AgentGrade benchmark recommended"],
        }
    if tier == "LOW":
        return {
            "product": "ClawCheck Free Snapshot",
            "ladder": ladder,
            "required_review": ["Permission map · routine review · graduate to AgentGrade when commercial use begins"],
        }
    return {
        "product": "—",
        "ladder": ladder,
        "required_review": [],
    }
