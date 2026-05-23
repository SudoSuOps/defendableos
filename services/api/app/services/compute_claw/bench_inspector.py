"""BenchInspector · benchmark evidence attachment foundation.

Per the build spec: do not run hardware benchmarks from the web in this
sprint. The Defendable Box / AgentGrade CLI already produces benchmark
receipts under data/agentgrade-receipts/. This module:

  · defines the attachment schema
  · records owner-attested-vs-Defendable-tested distinction
  · writes the benchmark-evidence pointer immutably to the bakery vault
  · NEVER claims tested-condition unless a benchmark receipt path is supplied

Doctrine:
  · Without a benchmark receipt, condition is ATTESTED ONLY · the agent
    cannot claim Defendable-tested condition for the asset
  · Owner-supplied benchmark file requires verification before
    condition_claim_verified=True · this module records the pending state
"""
from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass
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


BENCHMARK_STATUSES: tuple[str, ...] = (
    "NOT_YET_RUN",
    "OPERATOR_SUPPLIED_PENDING_VERIFICATION",
    "DEFENDABLE_TESTED_VERIFIED",
)


@dataclass
class BenchmarkEvidence:
    benchmark_evidence_id: str
    asset_intake_id: str
    benchmark_type: str                # e.g., DEFENDABLE_COMPUTE_INSPECTION
    machine_identity_hash: str | None
    gpu_model_observed: str | None
    vram_observed_gb: int | None
    benchmark_run_id: str | None
    benchmark_status: str
    receipt_path: str | None
    condition_claim_verified: bool
    captured_at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class BenchmarkAttachError(ValueError):
    pass


def _new_evidence_id() -> str:
    return f"DBENCH-{uuid.uuid4().hex[:14].upper()}"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def attach_benchmark_evidence(
    *,
    asset_intake_id: str,
    benchmark_type: str = "DEFENDABLE_COMPUTE_INSPECTION",
    machine_identity_hash: str | None = None,
    gpu_model_observed: str | None = None,
    vram_observed_gb: int | None = None,
    benchmark_run_id: str | None = None,
    receipt_path: str | None = None,
    verified: bool = False,
    store: BakeryStore | None = None,
) -> tuple[BenchmarkEvidence, dict[str, Any]]:
    """Record a benchmark-evidence pointer.

    `verified=True` is only honored when a receipt_path is provided. The
    doctrine: Defendable-tested condition requires a verifiable receipt.
    Without one, condition_claim_verified stays False.
    """
    if not asset_intake_id or not isinstance(asset_intake_id, str):
        raise BenchmarkAttachError("asset_intake_id is required")
    if benchmark_type not in (
        "DEFENDABLE_COMPUTE_INSPECTION",
        "DEFENDABLE_AGENTGRADE_BENCH",
        "OPERATOR_SUPPLIED_THIRD_PARTY",
    ):
        raise BenchmarkAttachError(
            "benchmark_type must be one of: DEFENDABLE_COMPUTE_INSPECTION · "
            "DEFENDABLE_AGENTGRADE_BENCH · OPERATOR_SUPPLIED_THIRD_PARTY"
        )

    # Status logic
    if receipt_path and verified:
        status = "DEFENDABLE_TESTED_VERIFIED"
        condition_claim_verified = True
    elif receipt_path:
        status = "OPERATOR_SUPPLIED_PENDING_VERIFICATION"
        condition_claim_verified = False
    else:
        status = "NOT_YET_RUN"
        condition_claim_verified = False

    evidence = BenchmarkEvidence(
        benchmark_evidence_id=_new_evidence_id(),
        asset_intake_id=asset_intake_id,
        benchmark_type=benchmark_type,
        machine_identity_hash=machine_identity_hash,
        gpu_model_observed=gpu_model_observed,
        vram_observed_gb=vram_observed_gb,
        benchmark_run_id=benchmark_run_id,
        benchmark_status=status,
        receipt_path=receipt_path,
        condition_claim_verified=condition_claim_verified,
        captured_at=_now_iso(),
    )

    store = store or get_bakery_store()
    body = json.dumps(evidence.to_dict(), sort_keys=True, indent=2).encode("utf-8")
    key = bakery_key(
        "compute-claw", "benchmark-evidence",
        f"{safe_key_part(evidence.benchmark_evidence_id)}.json",
    )
    artifact = store.driver.write_immutable(key, body, "application/json")

    receipt = generate_receipt(
        artifact_type="pair_candidate",
        artifact_key=artifact.key,
        artifact_bytes=body,
        source_run_id=asset_intake_id,
        tribunal_label="VERIFIED" if condition_claim_verified else "PENDING_VERIFICATION",
        redaction_status="NOT_APPLICABLE",
        consent_status={"benchmark_evidence_pointer": True},
        extra_metadata={
            "rail": "compute_claw.benchmark_evidence",
            "benchmark_evidence_id": evidence.benchmark_evidence_id,
            "asset_intake_id": asset_intake_id,
            "status": status,
        },
        store=store,
    )
    append_event(
        event_type="clawcheck.receipt.generated",
        run_id=asset_intake_id,
        payload={
            "rail": "computeclaw.benchmark_evidence.attached",
            "benchmark_evidence_id": evidence.benchmark_evidence_id,
            "status": status,
            "receipt_id": receipt["receipt_id"],
        },
        store=store,
    )

    envelope = {
        "benchmark_evidence_id": evidence.benchmark_evidence_id,
        "artifact_key": artifact.key,
        "artifact_sha256": artifact.sha256,
        "receipt_id": receipt["receipt_id"],
        "status": status,
        "condition_claim_verified": condition_claim_verified,
    }
    return evidence, envelope
