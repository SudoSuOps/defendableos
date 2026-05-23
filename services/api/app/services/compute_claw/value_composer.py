"""ValueComposer · draft AIOV Proof Pack assembly.

Composes an evidence-summary draft from:
  · ComputeIntake (owner-attested)
  · MarketScout observations (asking-price evidence only)
  · BenchmarkEvidence pointer (tested-condition gate)
  · UtilityEvidence pointer (income evidence gate)

ALWAYS produces a DRAFT. Never issues a final value number, never
issues a deed. The output is a structured report + a readiness status
indicating what evidence is still missing before Validator review.
"""
from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any

from app.services.claw_bakery.bakery_storage import (
    BakeryStore,
    bakery_key,
    get_bakery_store,
    safe_key_part,
)
from app.services.claw_bakery.bakery_events import append_event
from app.services.claw_bakery.receipts import generate_receipt


READINESS_STATUSES: tuple[str, ...] = (
    "INTAKE_ONLY",
    "MARKET_EVIDENCE_COLLECTED",
    "BENCHMARK_REQUIRED",
    "UTILITY_EVIDENCE_OPTIONAL",
    "READY_FOR_VALIDATOR_REVIEW",
    "DEED_ELIGIBILITY_REVIEW_REQUIRED",
)


@dataclass
class AIOVDraft:
    aiov_draft_id: str
    asset_intake_id: str
    captured_at: str
    asset_identity: dict[str, Any]
    observed_market_evidence: dict[str, Any]
    benchmark_evidence: dict[str, Any]
    utility_evidence: dict[str, Any]
    aiov_readiness: dict[str, Any]
    status_flags: list[str] = field(default_factory=list)
    doctrine_note: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_draft_id() -> str:
    return f"AIOV-DRAFT-{uuid.uuid4().hex[:14].upper()}"


def compose_draft(
    *,
    intake: dict[str, Any],
    market_observation_summary: dict[str, Any] | None = None,
    benchmark_evidence: dict[str, Any] | None = None,
    utility_evidence: dict[str, Any] | None = None,
    store: BakeryStore | None = None,
) -> tuple[AIOVDraft, dict[str, Any]]:
    """Build a draft AIOV Proof Pack envelope and persist it.

    All inputs are dicts (the dataclass-to-dict shape from the upstream
    modules) so this composer is decoupled from the source types.
    """
    asset_intake_id = intake.get("asset_intake_id")
    if not asset_intake_id:
        raise ValueError("intake.asset_intake_id is required")

    captured_at = _now_iso()

    # ── Asset identity block (owner-attested) ────────────────────────
    missing_identity = []
    if not intake.get("evidence_supplied", {}).get("photos"):
        missing_identity.append("identity_photos")
    if not intake.get("evidence_supplied", {}).get("serial_hash"):
        missing_identity.append("serial_hash")

    asset_identity = {
        "owner_attested": True,
        "asset_type": intake.get("asset_type"),
        "asset_category": intake.get("asset_category"),
        "manufacturer": intake.get("manufacturer"),
        "model_name": intake.get("model_name"),
        "vram_gb_claimed": intake.get("vram_gb"),
        "quantity": intake.get("quantity"),
        "condition_claimed": intake.get("condition_claimed"),
        "missing_identity_evidence": missing_identity,
    }

    # ── Observed market evidence block (eBay Browse only) ────────────
    if market_observation_summary:
        market_block = {
            "source": "EBAY_BROWSE_API",
            "evidence_type": "OBSERVED_ASKING_PRICE_EVIDENCE",
            "transaction_verified": False,
            "condition_verified_by_defendable": False,
            "batch_summary": market_observation_summary,
            "disclaimer": (
                "Observed active listing evidence only. Asking prices are not "
                "verified paid transaction comps. Seller-stated condition is "
                "not Defendable-verified condition."
            ),
        }
    else:
        market_block = {
            "source": "EBAY_BROWSE_API",
            "evidence_type": "OBSERVED_ASKING_PRICE_EVIDENCE",
            "status": "NOT_YET_COLLECTED",
        }

    # ── Benchmark evidence block ─────────────────────────────────────
    if benchmark_evidence:
        bench_block = {
            **benchmark_evidence,
            "doctrine_note": (
                "Only DEFENDABLE_TESTED_VERIFIED supports tested-condition claims. "
                "Other states are pointer-only."
            ),
        }
        benchmark_status_for_aiov = benchmark_evidence.get(
            "benchmark_status", "NOT_YET_RUN"
        )
    else:
        bench_block = {
            "status": "NOT_YET_ATTACHED",
            "doctrine_note": "A benchmark receipt is required to support any Defendable-tested condition claim.",
        }
        benchmark_status_for_aiov = "NOT_YET_RUN"

    # ── Utility evidence block ───────────────────────────────────────
    if utility_evidence:
        util_block = {
            **utility_evidence,
            "doctrine_note": (
                "Only DEFENDABLE_FLEET_RECEIPT_VERIFIED supports income claims. "
                "OPERATOR_SUPPLIED_UNVERIFIED is preserved but marked as such."
            ),
        }
        utility_status_for_aiov = utility_evidence.get("evidence_status", "NOT_SUPPLIED")
    else:
        util_block = {
            "status": "NOT_SUPPLIED",
            "doctrine_note": "Optional · improves AIOV draft when verified evidence is attached.",
        }
        utility_status_for_aiov = "NOT_SUPPLIED"

    # ── Readiness status (drives next-step recommendation) ───────────
    if market_observation_summary is None:
        readiness = "INTAKE_ONLY"
    elif benchmark_status_for_aiov == "DEFENDABLE_TESTED_VERIFIED":
        readiness = "READY_FOR_VALIDATOR_REVIEW"
    elif benchmark_status_for_aiov in (
        "OPERATOR_SUPPLIED_PENDING_VERIFICATION", "NOT_YET_RUN",
    ):
        readiness = "BENCHMARK_REQUIRED"
    else:
        readiness = "MARKET_EVIDENCE_COLLECTED"

    # The intake-only path means market evidence not collected yet
    if readiness == "INTAKE_ONLY":
        missing = [
            "observed_market_evidence",
            "benchmark_receipt",
            "utility_evidence (optional)",
        ]
        unsupportable = ["any Defendable-tested condition claim", "any final value opinion"]
    elif readiness == "BENCHMARK_REQUIRED":
        missing = ["benchmark_receipt", "utility_evidence (optional)"]
        unsupportable = ["Defendable-tested condition claim"]
    elif readiness == "READY_FOR_VALIDATOR_REVIEW":
        missing = ["validator_review", "utility_evidence (optional)"]
        unsupportable = []
    else:
        missing = ["benchmark_receipt"]
        unsupportable = ["Defendable-tested condition claim"]

    aiov_readiness = {
        "readiness_status": readiness,
        "evidence_present": _present_evidence(intake, market_observation_summary, benchmark_evidence, utility_evidence),
        "evidence_missing": missing,
        "findings_not_yet_supported": unsupportable,
        "validator_next_steps": [
            "Operator reviews any flagged exclusions in market batch",
            "Defendable runs / verifies benchmark for tested-condition claim",
            "Validator review chain · 12-check doctrine",
            "On pass: Defendable Compute Deed eligibility review",
        ],
        "automated_decision": (
            "NONE. No final value opinion is issued by this draft. "
            "No Defendable Deed is issued by this draft."
        ),
    }

    status_flags = [
        "DRAFT_ONLY",
        "NO_FINAL_VALUE_OPINION_ISSUED",
        "NO_DEFENDABLE_DEED_ISSUED",
        "ACTIVE_LISTINGS_ARE_NOT_SOLD_COMPS",
    ]
    if benchmark_status_for_aiov != "DEFENDABLE_TESTED_VERIFIED":
        status_flags.append("CONDITION_NOT_DEFENDABLE_TESTED")
    if utility_status_for_aiov != "DEFENDABLE_FLEET_RECEIPT_VERIFIED":
        status_flags.append("UTILITY_NOT_DEFENDABLE_VERIFIED")

    draft = AIOVDraft(
        aiov_draft_id=_new_draft_id(),
        asset_intake_id=asset_intake_id,
        captured_at=captured_at,
        asset_identity=asset_identity,
        observed_market_evidence=market_block,
        benchmark_evidence=bench_block,
        utility_evidence=util_block,
        aiov_readiness=aiov_readiness,
        status_flags=status_flags,
        doctrine_note=(
            "DEFENDABLE COMPUTE PROOF PACK · DRAFT. Active listings are "
            "observed asking-price evidence · NOT sold comps. No final "
            "value opinion is issued. No deed is issued. Validator review "
            "is required before any deed eligibility determination."
        ),
    )

    # Persist immutably
    store = store or get_bakery_store()
    body = json.dumps(draft.to_dict(), sort_keys=True, indent=2).encode("utf-8")
    key = bakery_key(
        "compute-claw", "aiov-drafts",
        f"{safe_key_part(draft.aiov_draft_id)}.json",
    )
    artifact = store.driver.write_immutable(key, body, "application/json")

    receipt = generate_receipt(
        artifact_type="pair_candidate",
        artifact_key=artifact.key,
        artifact_bytes=body,
        source_run_id=asset_intake_id,
        tribunal_label="DRAFT",
        redaction_status="NOT_APPLICABLE",
        consent_status={"aiov_draft": True},
        extra_metadata={
            "rail": "compute_claw.aiov_draft",
            "aiov_draft_id": draft.aiov_draft_id,
            "asset_intake_id": asset_intake_id,
            "readiness_status": readiness,
        },
        store=store,
    )
    append_event(
        event_type="clawcheck.receipt.generated",
        run_id=asset_intake_id,
        payload={
            "rail": "computeclaw.aiov_draft.generated",
            "aiov_draft_id": draft.aiov_draft_id,
            "readiness_status": readiness,
            "receipt_id": receipt["receipt_id"],
        },
        store=store,
    )

    envelope = {
        "aiov_draft_id": draft.aiov_draft_id,
        "artifact_key": artifact.key,
        "artifact_sha256": artifact.sha256,
        "receipt_id": receipt["receipt_id"],
        "readiness_status": readiness,
        "status_flags": status_flags,
    }
    return draft, envelope


def _present_evidence(intake, market, bench, util) -> list[str]:
    present = []
    if intake:
        present.append("intake")
        ev = intake.get("evidence_supplied", {}) or {}
        if ev.get("photos"):
            present.append("identity_photos")
        if ev.get("serial_hash"):
            present.append("serial_hash")
    if market:
        present.append("market_evidence")
    if bench:
        bs = bench.get("benchmark_status", "")
        if bs == "DEFENDABLE_TESTED_VERIFIED":
            present.append("benchmark_verified")
        elif bs == "OPERATOR_SUPPLIED_PENDING_VERIFICATION":
            present.append("benchmark_pending")
    if util:
        us = util.get("evidence_status", "")
        if us == "DEFENDABLE_FLEET_RECEIPT_VERIFIED":
            present.append("utility_verified")
        elif us == "OPERATOR_SUPPLIED_UNVERIFIED":
            present.append("utility_unverified")
    return present
