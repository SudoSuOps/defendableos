"""Typed tool-use contracts for DefendableOS workflows.

Kimi K2.6 (and OpenAI gpt-4o-class models) support function calling. We use it
to enforce DefendableOS doctrine at the JSON Schema level rather than relying
on prompt discipline alone:

  · Severities are enums · the model cannot invent "CRITICAL" or "URGENT".
  · evidence_classification is an enum · listings can never be relabelled.
  · Tool names + check IDs match our deterministic constants exactly.

Each contract returns a `ToolDefinition` ready to be passed to the gateway.
"""
from __future__ import annotations

from app.integrations.model_gateway import ToolDefinition
from app.models.research import EvidenceClassification
from app.services.validator_checks import CHECKS


# ─────────────────────────────────────────────────────────────────────────────
# Validator-assist · model surfaces additional findings the deterministic
# checks can't see (e.g. "this manufacturer spec contradicts the benchmark").
# ─────────────────────────────────────────────────────────────────────────────

VALIDATOR_FLAG_TOOL = ToolDefinition(
    name="flag_finding",
    description=(
        "Surface a concern the model identifies in the supplied AIOV draft + "
        "evidence. Use only when there is a specific, citeable issue. Do NOT "
        "invent findings. Do NOT promise certification or warranty. Severities "
        "are bounded: BLOCKING is reserved for unsupported value claims, "
        "listing-as-sale, or missing asset identity."
    ),
    parameters={
        "type": "object",
        "properties": {
            "check": {
                "type": "string",
                "enum": list(CHECKS),
                "description": "Which canonical check the finding relates to.",
            },
            "severity": {
                "type": "string",
                "enum": ["INFO", "LOW", "MEDIUM", "HIGH", "BLOCKING"],
            },
            "finding": {
                "type": "string",
                "description": "One concise sentence describing the concern.",
                "minLength": 12,
                "maxLength": 500,
            },
            "evidence_refs": {
                "type": "array",
                "items": {"type": "string"},
                "description": (
                    "List of source_id / evidence_item_id strings supporting "
                    "or contradicting the finding. Empty list is allowed only "
                    "when the finding is structural (e.g. missing manifest)."
                ),
            },
        },
        "required": ["check", "severity", "finding", "evidence_refs"],
        "additionalProperties": False,
    },
)


# ─────────────────────────────────────────────────────────────────────────────
# Research-synthesis · classify each public source AFTER Brave returns them.
# Without this every source starts as UNKNOWN and the validator flags it.
# ─────────────────────────────────────────────────────────────────────────────

RESEARCH_CLASSIFY_TOOL = ToolDefinition(
    name="classify_source",
    description=(
        "Classify a single public web research source by what kind of "
        "evidence it actually is. Be conservative · choose UNKNOWN over "
        "guessing. NEVER classify a listing price as a confirmed sale."
    ),
    parameters={
        "type": "object",
        "properties": {
            "source_id": {
                "type": "string",
                "description": "The research source UUID supplied in the prompt.",
            },
            "classification": {
                "type": "string",
                "enum": [c.value for c in EvidenceClassification],
            },
            "supports_claim": {
                "type": "string",
                "description": (
                    "Short label naming what this source supports · e.g. "
                    "'manufacturer_spec', 'recent_market_listing', "
                    "'auction_result_with_premium', 'review_commentary'."
                ),
                "maxLength": 120,
            },
            "rationale": {
                "type": "string",
                "description": "One sentence justifying the classification.",
                "minLength": 8,
                "maxLength": 400,
            },
        },
        "required": ["source_id", "classification", "supports_claim", "rationale"],
        "additionalProperties": False,
    },
)
