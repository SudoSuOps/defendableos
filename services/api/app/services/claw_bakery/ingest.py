"""Claw Bakery ingest · entry points called by the ClawCheck API path.

This module wires the existing intake/snapshot flow into the bakery
pipeline. The intake endpoint stays the source of truth for what's
shown to the operator; the bakery layer is additive:

  1. ingest_intake_turn(...)     · writes immutable raw intake JSON
  2. ingest_snapshot(...)        · writes immutable raw snapshot JSON +
                                   creates a PENDING pair candidate +
                                   emits events + generates receipts

All writes are best-effort: a failure inside ingest_* must NEVER fail
the user-facing intake turn. The endpoint catches and logs; the
operator's snapshot is returned regardless of bakery success.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from app.services.claw_bakery.bakery_events import append_event
from app.services.claw_bakery.bakery_storage import BakeryStore, get_bakery_store
from app.services.claw_bakery.pair_factory import (
    create_pair_candidate_from_snapshot,
)
from app.services.claw_bakery.receipts import generate_receipt


_log = logging.getLogger("claw_bakery.ingest")


def _run_id() -> str:
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    return f"cc_run_{ts}_{uuid.uuid4().hex[:8]}"


def ingest_intake_turn(
    *,
    user_message: str,
    findings: dict[str, Any],
    intake_complete: bool,
    refusal_reason: str | None,
    judge_provider: dict[str, Any],
    consent: dict[str, bool] | None = None,
    store: BakeryStore | None = None,
) -> dict[str, Any] | None:
    """Persist a single intake turn. Returns the bakery envelope or None
    on failure (callers must NOT fail the user response on a None).
    """
    try:
        store = store or get_bakery_store()
        run_id = _run_id()
        payload = {
            "run_id": run_id,
            "user_message_truncated": (user_message or "")[:4000],
            "findings": findings or {},
            "intake_complete": intake_complete,
            "refusal_reason": refusal_reason,
            "judge_provider": judge_provider,
            "consent": consent or {
                "store_for_snapshot": True,
                "allow_deidentified_training_use": False,
                "allow_evaluation_use": False,
            },
            "captured_at": datetime.now(timezone.utc).isoformat(),
        }
        artifact = store.put_raw_intake(run_id, payload)
        append_event(
            event_type="clawcheck.intake.completed",
            run_id=run_id,
            payload={
                "intake_complete": intake_complete,
                "judge_provider": judge_provider,
                "artifact_key": artifact.key,
                "artifact_sha256": artifact.sha256,
            },
            store=store,
        )
        return {
            "run_id": run_id,
            "artifact_key": artifact.key,
            "artifact_sha256": artifact.sha256,
        }
    except Exception:  # noqa: BLE001
        _log.exception("ingest_intake_turn failed · operator response unaffected")
        return None


def ingest_snapshot(
    *,
    run_id: str,
    snapshot: dict[str, Any],
    consent: dict[str, bool] | None = None,
    store: BakeryStore | None = None,
) -> dict[str, Any] | None:
    """Persist a completed snapshot, mint a PENDING pair candidate, emit
    events, and generate the receipt bundle. Returns the bakery envelope
    or None on failure.
    """
    try:
        store = store or get_bakery_store()
        snapshot_payload = {
            "run_id": run_id,
            "snapshot": snapshot,
            "captured_at": datetime.now(timezone.utc).isoformat(),
        }
        snap_artifact = store.put_raw_snapshot(run_id, snapshot_payload)
        append_event(
            event_type="clawcheck.snapshot.computed",
            run_id=run_id,
            payload={
                "tier": (snapshot.get("risk") or {}).get("tier"),
                "rule_id": (snapshot.get("risk") or {}).get("rule_id"),
                "artifact_key": snap_artifact.key,
                "artifact_sha256": snap_artifact.sha256,
            },
            store=store,
        )
        # Mint pair candidate (always PENDING · operator consent enforced inside)
        pair = create_pair_candidate_from_snapshot(
            source_run_id=run_id,
            snapshot=snapshot,
            input_record_key=None,  # the intake artifact key could be passed here
            raw_snapshot_key=snap_artifact.key,
            operator_consent=consent,
            store=store,
        )
        # Receipt for the snapshot itself
        snap_bytes = store.driver.read(snap_artifact.key)
        receipt = generate_receipt(
            artifact_type="snapshot",
            artifact_key=snap_artifact.key,
            artifact_bytes=snap_bytes,
            source_run_id=run_id,
            tribunal_label="PENDING",
            redaction_status="PENDING",
            consent_status=consent or {},
            store=store,
        )
        append_event(
            event_type="clawcheck.receipt.generated",
            run_id=run_id,
            payload={
                "receipt_id": receipt["receipt_id"],
                "artifact_type": "snapshot",
                "sha256": receipt["sha256"],
            },
            store=store,
        )
        # Validator review-request event (admin queue marker only · no auto-validate)
        append_event(
            event_type="clawcheck.validator.review_requested",
            run_id=run_id,
            payload={
                "pair_id": pair.pair_id,
                "risk_class": pair.risk_class,
                "domain": pair.domain,
            },
            store=store,
        )
        return {
            "run_id": run_id,
            "snapshot_artifact_key": snap_artifact.key,
            "snapshot_sha256": snap_artifact.sha256,
            "pair_id": pair.pair_id,
            "pair_label": pair.tribunal_label,
            "receipt_id": receipt["receipt_id"],
        }
    except Exception:  # noqa: BLE001
        _log.exception("ingest_snapshot failed · operator response unaffected")
        return None


def safe_public_metrics(store: BakeryStore | None = None) -> dict[str, Any]:
    """Aggregate-only counts safe to render publicly. Never includes
    operator_attested_context, agent names, or any artifact content."""
    store = store or get_bakery_store()
    try:
        intakes = len(store.list_under("raw-evidence/intakes"))
        snapshots = len(store.list_under("raw-evidence/snapshots"))
        pending = len(store.list_pair_candidates("pending"))
        honey = len(store.list_pair_candidates("honey"))
        jelly = len(store.list_pair_candidates("jelly"))
        jelly_rep = len(store.list_pair_candidates("jelly-repaired"))
        propolis = len(store.list_pair_candidates("propolis-failures"))
        receipts = len(store.list_under("receipts/sha256"))
        releases = len(store.list_under("dataset-releases"))
        events = len(store.list_under("events"))
    except Exception:  # noqa: BLE001
        # Storage misconfigured · serve zeros · log internally
        _log.exception("safe_public_metrics list failed · returning zeros")
        intakes = snapshots = pending = honey = jelly = jelly_rep = propolis = receipts = releases = events = 0
    # Benchmark-run metrics · best-effort
    try:
        from app.services.claw_bakery.benchmark_ingest import safe_benchmark_metrics
        bench = safe_benchmark_metrics(store=store)
    except Exception:  # noqa: BLE001
        _log.exception("safe_benchmark_metrics failed · returning zeros")
        bench = {
            "benchmark_runs_total": 0,
            "propolis_denied_runs": 0,
            "candidate_runs_pending_validator": 0,
            "controlled_demonstration": True,
        }
    return {
        "intakes_captured": intakes,
        "snapshots_generated": snapshots,
        "pending_pair_candidates": pending,
        "honey_pair_candidates": honey,
        "jelly_pair_candidates": jelly,
        "jelly_repaired_to_honey": jelly_rep,
        "propolis_failures": propolis,
        "receipts_hashed": receipts,
        "dataset_releases": releases,
        "events_recorded": events,
        "benchmark_lanes": ["business_agent_v1", "refund_agent_v1", "coding_ops_agent_v1"],
        "benchmark_runs_total": bench["benchmark_runs_total"],
        "propolis_denied_runs": bench["propolis_denied_runs"],
        "candidate_runs_pending_validator": bench["candidate_runs_pending_validator"],
        "controlled_demonstration_label": "Controlled Demonstration / Not Customer Production Evidence",
    }
