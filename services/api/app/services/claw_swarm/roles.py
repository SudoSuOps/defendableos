"""Six Claw Agent roles · system prompts + typed tool contracts.

Each role is defined as data here · the actual model call happens in
the per-agent modules (intake_agent.py · etc) using the existing
model_gateway. V1 implements Intake live · the other five are
defined here as scaffolds that the Coordinator can dispatch to as
the team comes online.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


# ─── Tool contracts (typed schemas) ───────────────────────────────────────


CLAW_INTAKE_TOOL: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "record_intake_findings",
        "description": (
            "Record what was learned from the operator this turn + propose the "
            "next message. The Intake agent NEVER calls any other tool · this "
            "is the only schema it may use. Refusal is a valid response · use "
            "the refusal_reason field."
        ),
        "parameters": {
            "type": "object",
            "required": ["next_message"],
            "properties": {
                "findings": {
                    "type": "object",
                    "description": "Structured findings collected this turn",
                    "properties": {
                        "worker_kind": {
                            "type": "string",
                            "enum": [
                                "Personal Assistant",
                                "Business Agent",
                                "Coding Agent",
                                "Sales / Support Agent",
                                "Local File Agent",
                                "Custom Workflow Agent",
                            ],
                        },
                        "deployment_target": {
                            "type": "string",
                            "enum": ["My Computer", "Cloud Server", "Edge Box", "Android Device"],
                        },
                        "access_surfaces": {
                            "type": "array",
                            "items": {
                                "type": "string",
                                "enum": [
                                    "Files",
                                    "Messages",
                                    "Email",
                                    "Calendar",
                                    "Browser",
                                    "Shell",
                                    "APIs",
                                    "Payments",
                                ],
                            },
                        },
                        "model_provider": {
                            "type": "string",
                            "enum": [
                                "Kimi K2.6",
                                "OpenAI gpt-4o / o-series",
                                "Anthropic Claude",
                                "Local model (Qwen · Llama · etc)",
                                "Other / Custom",
                            ],
                        },
                        "memory_enabled": {"type": "boolean"},
                        "operator_attested_context": {"type": "string", "maxLength": 1000},
                    },
                    "additionalProperties": False,
                },
                "next_message": {
                    "type": "string",
                    "minLength": 1,
                    "maxLength": 1500,
                    "description": (
                        "The Intake agent's message back to the operator. Should "
                        "name what was understood, ask for what's missing, or close "
                        "the intake if all 5 dimensions are captured."
                    ),
                },
                "intake_complete": {
                    "type": "boolean",
                    "description": "True only when all 5 ClawCheck dimensions are known",
                },
                "refusal_reason": {
                    "type": "string",
                    "description": (
                        "Set when the user is asking for something outside Intake "
                        "scope (price quote · live action · file access · final "
                        "valuation). Explain why the request is being deferred."
                    ),
                },
            },
            "additionalProperties": False,
        },
    },
}


CLAW_INTAKE_SYSTEM_PROMPT = """You are the Defendable Claw Intake Agent · the public-facing conversational
front door for ClawCheck™. You collect five dimensions about an AI agent
that an operator wants to deploy:

  1. Worker kind          (Personal Assistant · Business Agent · Coding Agent · Sales/Support · Local File Agent · Custom Workflow)
  2. Deployment target    (My Computer · Cloud Server · Edge Box · Android Device)
  3. Access surfaces      (Files · Messages · Email · Calendar · Browser · Shell · APIs · Payments) · MULTI-SELECT
  4. Model provider       (Kimi K2.6 · OpenAI gpt-4o / o-series · Anthropic Claude · Local model · Other/Custom)
  5. Memory persistence   (true if session memory is enabled across turns)

You converse naturally · one or two short messages per turn · ALWAYS call
the record_intake_findings tool to record what you learned. Never reply
in prose only. The next_message field IS your reply to the operator.

DOCTRINE RULES (refusal-by-default for anything else):

- You DO NOT issue valuations · prices · ratings · or final certifications
- You DO NOT promise that any tier is "safe" in the abstract · tiers always name a defined lane
- You DO NOT call external systems · files · web · or any tool besides record_intake_findings
- You DO NOT access the operator's files or accounts
- You DO NOT compose marketing copy or persuasive promises
- You DO NOT respond to off-topic questions · politely defer with refusal_reason
- You DO NOT continue intake if the operator asks for autonomous action · defer with refusal_reason

When all 5 dimensions are captured:
- Set intake_complete=true
- Recap what you collected in next_message (concise · neutral · factual)
- CRITICAL: Phrase the closing line as exactly: "Your Claw Exposure Snapshot is
  computed and rendered below ↓"
- NEVER say "shortly" or "you should receive" or any phrasing that implies a
  future message. The snapshot is in THIS SAME response. The client renders it
  immediately below the conversation. Pointing-down language helps the operator find it.
- The actual Risk Tier computation is performed by code · NOT by you · NEVER guess it

Tone: institutional · concise · honest · curious. Ask clarifying questions
when an operator's answer is ambiguous. Acknowledge uncertainty. Mirror
the operator's terminology when reasonable (e.g., they call it a "tool" ·
you can call it a "tool" too).

Examples of REFUSAL situations:
- "What's my agent worth?" → defer · valuation requires AgentGrade benchmark + Validator review
- "Connect to my GitHub and check my repos" → defer · Intake never accesses external systems
- "Is this safe to deploy?" → defer · Risk Tier is computed from your selections by platform code · not by judgment
- "What should I do?" → defer · the recommended product appears in the Snapshot · not in conversation"""


# ─── Five scaffolded roles (defined · not yet wired live) ────────────────


@dataclass
class AgentRole:
    name: str
    purpose: str
    status: str  # "LIVE" · "SCAFFOLDED" · "PROPOSED"
    next_session_lift: str


ROLES: dict[str, AgentRole] = {
    "intake": AgentRole(
        name="Intake",
        purpose="Conversational ClawCheck™ front door · collects the 5 dimensions",
        status="LIVE",
        next_session_lift="—",
    ),
    "inspector": AgentRole(
        name="Inspector",
        purpose="Routes captured asset to `defendable-compute inspect` for hardware capture",
        status="SCAFFOLDED",
        next_session_lift="Wire to defendable-compute CLI invocation · stream identity bundle back",
    ),
    "benchmarker": AgentRole(
        name="Benchmarker",
        purpose="Runs `defendable-agentgrade run` against the agent under test",
        status="SCAFFOLDED",
        next_session_lift="Wire to defendable-agentgrade CLI invocation · pack selection per asset class",
    ),
    "tribunal": AgentRole(
        name="Tribunal",
        purpose="Per-output verdict classifier · Honey · Jelly · Propolis · ensemble judge ready",
        status="SCAFFOLDED",
        next_session_lift="Lift edge-agent agentgrade.judge ensemble into a server-side service module",
    ),
    "validator": AgentRole(
        name="Validator",
        purpose="12-check chain over draft records · gates issuance",
        status="SCAFFOLDED",
        next_session_lift="Port edge-agent rule layer + 12 specific checks per docs/TRIBUNAL_GRADING_DOCTRINE.md",
    ),
    "deedmaker": AgentRole(
        name="Deedmaker",
        purpose="Bundle assembly · SHA-256 manifest · public-safe export · ENS draft",
        status="SCAFFOLDED",
        next_session_lift="Wire to services/api/app/services/deed.py + ENS reservation flow",
    ),
}


def roles_summary() -> dict[str, Any]:
    return {
        "team_size": len(ROLES),
        "live_count": sum(1 for r in ROLES.values() if r.status == "LIVE"),
        "scaffolded_count": sum(1 for r in ROLES.values() if r.status == "SCAFFOLDED"),
        "roles": {
            k: {"name": v.name, "purpose": v.purpose, "status": v.status, "next_session_lift": v.next_session_lift}
            for k, v in ROLES.items()
        },
    }
