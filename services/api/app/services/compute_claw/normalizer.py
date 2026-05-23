"""ComputeClaw normalizer · noise/accessory/parts exclusion.

Deterministic + reviewable. Every observation gets:
  · decision: INCLUDED | EXCLUDED
  · reason_code: machine-readable reason for the decision
  · reason_text: human-readable explanation citing the title fragment
  · review_status: MACHINE_FILTERED_PENDING_REVIEW (operator can override)

Excluded observations are PRESERVED in storage with the reason · they are
NEVER deleted. The Validator review path lets an operator promote a wrongly
excluded observation back to INCLUDED with an audit trail.
"""
from __future__ import annotations

import re
from dataclasses import dataclass


# Phrases that mean "this isn't a working GPU/compute asset · likely
# accessory or parts-only listing". Order doesn't matter · we match
# each as a substring against the lowercased title.
EXCLUSION_PHRASES: tuple[tuple[str, str], ...] = (
    ("box only", "ACCESSORY_ONLY"),
    ("empty box", "ACCESSORY_ONLY"),
    ("heatsink only", "ACCESSORY_ONLY"),
    ("cooler only", "ACCESSORY_ONLY"),
    ("fan only", "ACCESSORY_ONLY"),
    ("backplate only", "ACCESSORY_ONLY"),
    ("waterblock only", "ACCESSORY_ONLY"),
    ("water block only", "ACCESSORY_ONLY"),
    ("bracket only", "ACCESSORY_ONLY"),
    ("cable only", "ACCESSORY_ONLY"),
    ("for parts", "BROKEN_OR_PARTS"),
    ("parts only", "BROKEN_OR_PARTS"),
    ("not working", "BROKEN_OR_PARTS"),
    ("broken", "BROKEN_OR_PARTS"),
    ("repair", "BROKEN_OR_PARTS"),  # often "needs repair" or "for repair"
    ("no gpu", "MISSING_CORE_ASSET"),
)


@dataclass
class NormalizationDecision:
    decision: str               # INCLUDED | EXCLUDED
    reason_code: str | None     # ACCESSORY_ONLY · BROKEN_OR_PARTS · MISSING_CORE_ASSET · None
    reason_text: str | None
    review_status: str          # MACHINE_FILTERED_PENDING_REVIEW
    matched_phrase: str | None


def classify_title(title: str) -> NormalizationDecision:
    """Apply the exclusion phrase table to a single listing title."""
    t = (title or "").lower()
    for phrase, code in EXCLUSION_PHRASES:
        # word-boundary-ish: avoid matching inside larger benign words
        # ("repair" inside "irreparable" · not a concern here but safer)
        pat = re.compile(rf"(?<![a-z]){re.escape(phrase)}(?![a-z])")
        if pat.search(t):
            return NormalizationDecision(
                decision="EXCLUDED",
                reason_code=code,
                reason_text=(
                    f"Title contains {phrase!r}; not comparable to functioning "
                    f"compute hardware."
                ),
                review_status="MACHINE_FILTERED_PENDING_REVIEW",
                matched_phrase=phrase,
            )

    return NormalizationDecision(
        decision="INCLUDED",
        reason_code=None,
        reason_text=None,
        review_status="MACHINE_FILTERED_PENDING_REVIEW",
        matched_phrase=None,
    )


def build_normalization_record(
    *,
    observation_id: str,
    normalized_asset_name: str,
    decision: NormalizationDecision,
) -> dict:
    return {
        "observation_id": observation_id,
        "normalized_asset_name": normalized_asset_name,
        "decision": decision.decision,
        "reason_code": decision.reason_code,
        "reason_text": decision.reason_text,
        "review_status": decision.review_status,
        "matched_phrase": decision.matched_phrase,
        "doctrine_note": (
            "Machine-filtered. Excluded observations are preserved for review; "
            "they are NOT deleted. Operator may manually re-include via "
            "Validator review pathway."
        ),
    }
