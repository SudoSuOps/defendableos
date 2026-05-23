"""Risk Tier computation · matches the deterministic doctrine on /defend-the-claw.

NEVER computed by the model · always by code · per
docs/DEFENDABLE_AGENT_GRADE.md no-overclaim doctrine.
"""
from __future__ import annotations

from typing import Any


HIGH_RISK_SURFACES = {"Shell", "Payments"}
COMMS_SURFACES = {"Messages", "Email"}
WRITE_SURFACES = {"Files", "Shell", "Payments", "APIs"}


def compute_risk_tier(
    worker_kind: str | None,
    deployment_target: str | None,
    access_surfaces: list[str] | None,
    memory_enabled: bool | None,
) -> dict[str, Any]:
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
        reasons.append("Shell or Payments + outbound messaging = autonomous-action exposure")
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
        reasons.append("Persistent memory increases blast radius if injection succeeds · review memory governance")

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
