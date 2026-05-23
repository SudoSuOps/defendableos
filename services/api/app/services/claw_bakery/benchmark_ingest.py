"""Benchmark-run ingest · imports an AgentGrade run directory into the
Claw Bakery vault with immutable storage + receipts + linked pair candidate.

Inputs: a path to a completed `rar-*` run directory (produced by
`defendable-agentgrade run --pack packs/refund_agent_v1 --judge
deterministic-policy`). Outputs: an envelope describing every artifact
key, receipt id, pair-candidate id, and event id created.

Doctrine guarantees (enforced in code):
  · The 6 founder-spec output files (run_manifest, task_results,
    adversarial_results, tribunal_candidate_verdict, hard_fail_summary,
    sha256sums) are written under
    `claw-bakery/benchmark-runs/<pack_id>/<run_id>/` as immutable artifacts
  · Each file gets a SHA-256 receipt
  · A pair candidate is created linked to: source intake fixture (if
    provided) · risk snapshot (if provided) · pack id · run id · candidate
    Tribunal verdict · hard-fail status
  · PROPOLIS runs land the pair candidate in pair-candidates/propolis-failures/
    with eligible_for_training=False and eligible_for_adversarial_evaluation
    deferred to admin review
  · HONEY_CANDIDATE runs land in pair-candidates/pending/ with
    validator_status=PENDING and eligible_for_training=False until the full
    Validator + redaction + consent path completes
  · Raw intake or snapshot artifacts are NEVER overwritten
"""
from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.services.claw_bakery.bakery_events import append_event
from app.services.claw_bakery.bakery_storage import (
    BakeryStore,
    bakery_key,
    get_bakery_store,
    safe_key_part,
)
from app.services.claw_bakery.pair_factory import (
    RedactionStatus,
    TribunalLabel,
    ValidatorStatus,
    assign_tribunal_label,
    create_pair_candidate_from_snapshot,
    set_redaction_status,
    set_validator_status,
)
from app.services.claw_bakery.receipts import generate_receipt


_log = logging.getLogger("claw_bakery.benchmark_ingest")

# Founder-spec required files
_REQUIRED_FILES = (
    "run_manifest.json",
    "task_results.jsonl",
    "adversarial_results.jsonl",
    "tribunal_candidate_verdict.json",
    "hard_fail_summary.json",
    "sha256sums.txt",
)


def _ensure_benchmark_dirs(store: BakeryStore, pack_id: str, run_id: str) -> None:
    """Ensure the local-driver benchmark-runs subtree exists."""
    if store.driver.name != "local":
        return
    root = store.driver.root  # type: ignore[attr-defined]
    (root / "benchmark-runs" / safe_key_part(pack_id) / safe_key_part(run_id)).mkdir(
        parents=True, exist_ok=True
    )


def _benchmark_artifact_key(pack_id: str, run_id: str, filename: str) -> str:
    return bakery_key(
        "benchmark-runs",
        pack_id,
        run_id,
        filename,
    )


@dataclass
class BenchmarkIngestEnvelope:
    pack_id: str
    pack_version: str
    run_id: str
    agent_id: str
    final_verdict: str
    deployment_status: str
    deed_eligibility: str
    hard_fail_count: int
    benchmark_artifact_keys: dict[str, str]   # filename → bakery key
    receipt_ids: dict[str, str]               # filename → receipt id
    pair_id: str
    pair_tribunal_label: str
    pair_eligible_for_training: bool
    bundle_sha256: str
    events: list[str]


def ingest_benchmark_run(
    *,
    run_dir: Path,
    source_intake_fixture: str | None = None,
    source_snapshot_key: str | None = None,
    operator_consent: dict[str, bool] | None = None,
    store: BakeryStore | None = None,
) -> BenchmarkIngestEnvelope:
    """Ingest a completed `rar-*` run directory into the Bakery vault.

    Idempotent at the run_id level · immutable writes mean re-running this
    on the same run_dir raises KeyExistsError. Re-import requires a fresh
    run.
    """
    store = store or get_bakery_store()
    run_dir = Path(run_dir).resolve()
    if not run_dir.is_dir():
        raise FileNotFoundError(f"run_dir does not exist: {run_dir}")

    # Load the run_manifest to extract pack + agent metadata
    rm_path = run_dir / "run_manifest.json"
    if not rm_path.exists():
        raise FileNotFoundError(f"run_manifest.json missing in {run_dir}")
    run_manifest = json.loads(rm_path.read_text())
    pack_id = run_manifest["pack_id"]
    pack_version = run_manifest.get("pack_version", "unknown")
    run_id = run_manifest["run_id"]
    agent_id = run_manifest["agent_id"]

    # Cross-check the 6 required files
    missing = [fn for fn in _REQUIRED_FILES if not (run_dir / fn).exists()]
    if missing:
        raise FileNotFoundError(f"run_dir missing required files: {missing}")

    # Ensure benchmark-runs subtree (local-driver only)
    _ensure_benchmark_dirs(store, pack_id, run_id)

    events: list[str] = []

    # Event · run started (synthetic · we ingest post-run)
    ev = append_event(
        event_type="clawforge.candidate.generated"  # neutral · run already happened
        if agent_id.startswith("clawforge_")
        else "clawcheck.intake.completed",
        run_id=run_id,
        payload={"phase": "benchmark_ingest_started", "pack_id": pack_id, "agent_id": agent_id},
        store=store,
    )
    events.append(ev["event_id"])
    # Custom benchmark-event type · we re-use the typed channel that already exists
    # plus a synthetic 'completed' marker via the receipt event below.

    # Walk required files · write each immutably, generate a receipt
    benchmark_artifact_keys: dict[str, str] = {}
    receipt_ids: dict[str, str] = {}
    for fn in _REQUIRED_FILES:
        body = (run_dir / fn).read_bytes()
        key = _benchmark_artifact_key(pack_id, run_id, fn)
        artifact = store.driver.write_immutable(
            key,
            body,
            "application/json" if fn.endswith(".json") or fn.endswith(".jsonl") else "text/plain",
        )
        benchmark_artifact_keys[fn] = artifact.key
        receipt = generate_receipt(
            artifact_type="benchmark_pack",
            artifact_key=artifact.key,
            artifact_bytes=body,
            source_run_id=run_id,
            tribunal_label=run_manifest.get("pack_deployment_status", "PENDING"),
            redaction_status="NOT_APPLICABLE",
            consent_status=operator_consent or {},
            extra_metadata={"file": fn, "pack_id": pack_id, "pack_version": pack_version},
            store=store,
        )
        receipt_ids[fn] = receipt["receipt_id"]
        ev = append_event(
            event_type="clawcheck.receipt.generated",
            run_id=run_id,
            payload={
                "receipt_id": receipt["receipt_id"],
                "artifact_type": "benchmark_pack",
                "artifact_key": artifact.key,
                "sha256": receipt["sha256"],
                "file": fn,
            },
            store=store,
        )
        events.append(ev["event_id"])

    # Per-task raw outputs · best-effort · write under raw_outputs/ subtree
    raw_outputs_dir = run_dir / "raw_outputs"
    if raw_outputs_dir.is_dir():
        for p in sorted(raw_outputs_dir.glob("*.json")):
            body = p.read_bytes()
            key = bakery_key(
                "benchmark-runs", pack_id, run_id, "raw_outputs", p.name
            )
            try:
                store.driver.write_immutable(key, body, "application/json")
            except Exception:  # noqa: BLE001
                _log.exception("raw_outputs ingest failed for %s · continuing", p.name)

    # Compute a bundle sha256 over the (sorted) sha256 strings of the
    # 6 required files · this is the auditable single hash for the bundle.
    bundle_blob = "\n".join(
        f"{hashlib.sha256((run_dir / fn).read_bytes()).hexdigest()}  {fn}"
        for fn in sorted(_REQUIRED_FILES)
    ).encode("utf-8")
    bundle_sha256 = hashlib.sha256(bundle_blob).hexdigest()

    # ── Create the linked pair candidate ──────────────────────────────
    tv = json.loads((run_dir / "tribunal_candidate_verdict.json").read_text())
    final_verdict_str = tv.get("tribunal_candidate_verdict", "PENDING")
    deployment_status = tv.get("deployment_status", "PENDING")
    deed_eligibility = tv.get("deed_eligibility", "NOT_YET_ELIGIBLE")
    hard_fail_payload = json.loads((run_dir / "hard_fail_summary.json").read_text())
    hard_fail_count = hard_fail_payload.get("total_hard_fail_conditions_triggered", 0)

    # Synthesize a "snapshot" envelope so the pair-factory create function
    # can derive risk class + domain from it.
    snapshot_for_pair = {
        "captured": {
            "agent_name": agent_id,
            "worker_kind": "Sales / Support Agent",
            "deployment_target": "Benchmark Sandbox",
            "model_provider": "deterministic-mock",
        },
        "risk": {
            "rule_id": "HIGH_FINANCIAL_AUTONOMOUS_ACTION",
            "risk_class": "HIGH_FINANCIAL_AUTONOMOUS_ACTION",
            "tier": run_manifest.get("pack_risk_tier", "HIGH"),
        },
        "benchmark_context": {
            "pack_id": pack_id,
            "pack_version": pack_version,
            "run_id": run_id,
            "tribunal_candidate_verdict": final_verdict_str,
            "deployment_status": deployment_status,
            "deed_eligibility": deed_eligibility,
            "hard_fail_count": hard_fail_count,
        },
    }
    pair = create_pair_candidate_from_snapshot(
        source_run_id=run_id,
        snapshot=snapshot_for_pair,
        input_record_key=None,
        raw_snapshot_key=source_snapshot_key,
        operator_consent=operator_consent,
        store=store,
    )

    # Promote / demote the pair based on the benchmark verdict
    if final_verdict_str == "PROPOLIS":
        # Hard fail → PROPOLIS bucket · eligible_for_adversarial_evaluation
        # is left False here · admin review explicitly flips it.
        pair.hard_fail = True
        assign_tribunal_label(
            pair,
            label=TribunalLabel.PROPOLIS,
            reason=(
                f"Benchmark run {run_id} against pack {pack_id} produced "
                f"{hard_fail_count} hard-fail condition(s) · DENIED"
            ),
            store=store,
        )
    elif final_verdict_str == "HONEY_CANDIDATE_PENDING_VALIDATOR":
        # Stays PENDING · validator_status PENDING · NOT training-eligible
        set_validator_status(
            pair,
            status=ValidatorStatus.PENDING,
            reason=(
                f"Benchmark run {run_id} returned HONEY_CANDIDATE_PENDING_VALIDATOR · "
                f"Validator review required before deed eligibility"
            ),
            store=store,
        )
        # Mark redaction as NOT_APPLICABLE for the synthetic mock-agent run
        # (no operator PII captured) · re-evaluate when real-agent benchmark.
        set_redaction_status(
            pair,
            status=RedactionStatus.NOT_APPLICABLE,
            reason="Mock-agent benchmark · no operator PII captured",
            store=store,
        )
    elif final_verdict_str == "JELLY":
        assign_tribunal_label(
            pair,
            label=TribunalLabel.JELLY,
            reason=f"Benchmark run {run_id} produced JELLY-grade output · repair candidate",
            store=store,
        )

    # Always emit the validator review-requested event
    ev = append_event(
        event_type="clawcheck.validator.review_requested",
        run_id=run_id,
        payload={
            "pair_id": pair.pair_id,
            "risk_class": pair.risk_class,
            "domain": pair.domain,
            "benchmark_pack": pack_id,
            "tribunal_candidate_verdict": final_verdict_str,
        },
        store=store,
    )
    events.append(ev["event_id"])

    return BenchmarkIngestEnvelope(
        pack_id=pack_id,
        pack_version=pack_version,
        run_id=run_id,
        agent_id=agent_id,
        final_verdict=final_verdict_str,
        deployment_status=deployment_status,
        deed_eligibility=deed_eligibility,
        hard_fail_count=hard_fail_count,
        benchmark_artifact_keys=benchmark_artifact_keys,
        receipt_ids=receipt_ids,
        pair_id=pair.pair_id,
        pair_tribunal_label=pair.tribunal_label,
        pair_eligible_for_training=pair.eligible_for_training,
        bundle_sha256=bundle_sha256,
        events=events,
    )


# Public-safe aggregator · used by the bakery public_metrics endpoint
def safe_benchmark_metrics(store: BakeryStore | None = None) -> dict[str, Any]:
    """Aggregate-only counters for /claw-bakery to render. Never exposes
    raw prompts, agent reasoning, or artifact bodies."""
    store = store or get_bakery_store()
    try:
        run_keys = store.list_under("benchmark-runs")
    except Exception:  # noqa: BLE001
        run_keys = []
    # Count distinct run_ids (each run has multiple files)
    run_ids: set[str] = set()
    propolis_runs: set[str] = set()
    candidate_runs: set[str] = set()
    for k in run_keys:
        # Key shape: claw-bakery/benchmark-runs/<pack_id>/<run_id>/<file>
        parts = k.split("/")
        if len(parts) >= 5:
            rid = parts[3]
            run_ids.add(rid)
    # Inspect tribunal_candidate_verdict.json files for verdict counts
    for k in run_keys:
        if not k.endswith("tribunal_candidate_verdict.json"):
            continue
        try:
            payload = store.read_json(k)
            v = payload.get("tribunal_candidate_verdict")
            rid = payload.get("agent_id"), payload.get("captured_at")
            if v == "PROPOLIS":
                propolis_runs.add(str(rid))
            elif v == "HONEY_CANDIDATE_PENDING_VALIDATOR":
                candidate_runs.add(str(rid))
        except Exception:  # noqa: BLE001
            continue
    return {
        "benchmark_runs_total": len(run_ids),
        "propolis_denied_runs": len(propolis_runs),
        "candidate_runs_pending_validator": len(candidate_runs),
        "controlled_demonstration": True,
    }
