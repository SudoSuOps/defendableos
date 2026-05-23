"""Bakery benchmark-ingest tests.

Tests that a completed AgentGrade refund-run flows correctly into the
Bakery vault: immutable artifacts, deterministic receipts, linked pair
candidate, no training admission, no deed issuance.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def _bakery_tmp(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("CLAW_BAKERY_STORAGE_DRIVER", "local")
    monkeypatch.setenv("CLAW_BAKERY_LOCAL_ROOT", str(tmp_path / "bakery"))
    monkeypatch.setenv("CLAW_BAKERY_CLAWFORGE_ENABLED", "false")
    from app.services.claw_bakery import bakery_storage
    bakery_storage._store = None  # noqa: SLF001
    yield
    bakery_storage._store = None  # noqa: SLF001


def _write_run_dir(root: Path, *, run_id: str, agent_id: str, verdict: str, hard_fail_count: int) -> Path:
    """Synthesise a minimal but valid AgentGrade run_dir for ingest testing."""
    rd = root / run_id
    rd.mkdir(parents=True)
    (rd / "raw_outputs").mkdir()
    if verdict == "PROPOLIS":
        deployment, deed = "DENIED", "NOT_ELIGIBLE"
    elif verdict == "HONEY_CANDIDATE_PENDING_VALIDATOR":
        deployment, deed = "ELIGIBLE_FOR_VALIDATOR_REVIEW_ONLY", "NOT_YET_ELIGIBLE"
    else:
        deployment, deed = "PENDING", "NOT_YET_ELIGIBLE"
    run_manifest = {
        "run_id": run_id,
        "pack_id": "refund-agent-v1",
        "pack_version": "1.0",
        "pack_risk_tier": "HIGH",
        "pack_deployment_status": "RESTRICTED_PENDING_CONTROLS",
        "pack_deed_eligibility": "NOT_YET_ELIGIBLE",
        "agent_id": agent_id,
        "agent_version": "0.1.0-test",
        "agent_model_summary": {"model_name": "test-mock"},
        "agent_runtime_summary": {"inference_engine": "test"},
        "agent_tool_permissions": {"tools": []},
        "judge": {"kind": "deterministic-policy"},
        "task_count": 6,
        "adversarial_count": 6,
        "captured_at": "2026-05-23T12:00:00Z",
        "doctrine_seal": {"deed_issued_in_this_run": False},
    }
    (rd / "run_manifest.json").write_text(json.dumps(run_manifest, indent=2))
    (rd / "task_results.jsonl").write_text(
        json.dumps({"task_id": "t1", "per_task_verdict": verdict, "hard_fail_hit": hard_fail_count > 0}) + "\n"
    )
    (rd / "adversarial_results.jsonl").write_text(
        json.dumps({"case_id": "c1", "verdict": "COMPROMISED" if verdict == "PROPOLIS" else "RESISTED"}) + "\n"
    )
    (rd / "tribunal_candidate_verdict.json").write_text(
        json.dumps({
            "pack_id": "refund-agent-v1",
            "pack_version": "1.0",
            "agent_id": agent_id,
            "agent_version": "0.1.0-test",
            "captured_at": "2026-05-23T12:00:00Z",
            "tribunal_candidate_verdict": verdict,
            "deployment_status": deployment,
            "deed_eligibility": deed,
            "task_verdicts": [],
            "adversarial_verdicts": [],
            "honest_disclosure": [
                "Deterministic-policy judge · no LLM call",
                "Validator review is required",
                "No deed has issued",
            ],
        }, indent=2)
    )
    (rd / "hard_fail_summary.json").write_text(
        json.dumps({
            "total_hard_fail_conditions_triggered": hard_fail_count,
            "hard_fail_conditions_triggered": (
                ["refund_issued_without_human_approval"] * hard_fail_count
            )[:hard_fail_count],
            "propolis_tasks": [],
            "compromised_adversarial_cases": [],
            "resisted_adversarial_cases": [],
        }, indent=2)
    )
    (rd / "sha256sums.txt").write_text("placeholder\n")
    return rd


def test_ingest_unsafe_run_lands_in_propolis_bucket(tmp_path: Path) -> None:
    from app.services.claw_bakery.benchmark_ingest import ingest_benchmark_run
    from app.services.claw_bakery.bakery_storage import get_bakery_store
    rd = _write_run_dir(
        tmp_path / "runs",
        run_id="rar-test-unsafe-001",
        agent_id="unsafe-refund-agent",
        verdict="PROPOLIS",
        hard_fail_count=6,
    )
    env = ingest_benchmark_run(run_dir=rd)
    assert env.final_verdict == "PROPOLIS"
    assert env.deployment_status == "DENIED"
    assert env.deed_eligibility == "NOT_ELIGIBLE"
    assert env.pair_tribunal_label == "PROPOLIS"
    assert env.pair_eligible_for_training is False
    # Verify the pair landed in pair-candidates/propolis-failures/
    store = get_bakery_store()
    propolis = store.list_pair_candidates("propolis-failures")
    assert any(env.pair_id in k for k in propolis), (
        f"pair {env.pair_id} not in propolis bucket: {propolis}"
    )


def test_ingest_controlled_run_lands_in_pending_with_no_training_eligibility(tmp_path: Path) -> None:
    from app.services.claw_bakery.benchmark_ingest import ingest_benchmark_run
    from app.services.claw_bakery.bakery_storage import get_bakery_store
    rd = _write_run_dir(
        tmp_path / "runs",
        run_id="rar-test-controlled-001",
        agent_id="controlled-refund-draft-agent",
        verdict="HONEY_CANDIDATE_PENDING_VALIDATOR",
        hard_fail_count=0,
    )
    env = ingest_benchmark_run(run_dir=rd)
    assert env.final_verdict == "HONEY_CANDIDATE_PENDING_VALIDATOR"
    assert env.deployment_status == "ELIGIBLE_FOR_VALIDATOR_REVIEW_ONLY"
    assert env.deed_eligibility == "NOT_YET_ELIGIBLE"
    assert env.pair_tribunal_label == "PENDING"
    assert env.pair_eligible_for_training is False
    store = get_bakery_store()
    pending = store.list_pair_candidates("pending")
    assert any(env.pair_id in k for k in pending), (
        f"pair {env.pair_id} not in pending bucket: {pending}"
    )


def test_benchmark_artifacts_are_immutable(tmp_path: Path) -> None:
    from app.services.claw_bakery.bakery_storage import KeyExistsError
    from app.services.claw_bakery.benchmark_ingest import ingest_benchmark_run
    rd = _write_run_dir(
        tmp_path / "runs",
        run_id="rar-test-immut-001",
        agent_id="controlled-refund-draft-agent",
        verdict="HONEY_CANDIDATE_PENDING_VALIDATOR",
        hard_fail_count=0,
    )
    ingest_benchmark_run(run_dir=rd)
    # Re-ingest should fail because raw artifact already exists
    with pytest.raises(KeyExistsError):
        ingest_benchmark_run(run_dir=rd)


def test_benchmark_receipts_are_deterministic_per_artifact(tmp_path: Path) -> None:
    from app.services.claw_bakery.bakery_storage import get_bakery_store
    from app.services.claw_bakery.benchmark_ingest import ingest_benchmark_run
    rd = _write_run_dir(
        tmp_path / "runs",
        run_id="rar-test-recpt-001",
        agent_id="controlled-refund-draft-agent",
        verdict="HONEY_CANDIDATE_PENDING_VALIDATOR",
        hard_fail_count=0,
    )
    env = ingest_benchmark_run(run_dir=rd)
    store = get_bakery_store()
    for fn, key in env.benchmark_artifact_keys.items():
        body = store.driver.read(key)
        expected = hashlib.sha256(body).hexdigest()
        # The receipt under receipts/sha256/<receipt_id>.json should have this sha
        receipt_id = env.receipt_ids[fn]
        receipt_key = f"claw-bakery/receipts/sha256/{receipt_id}.json"
        receipt = store.read_json(receipt_key)
        assert receipt["sha256"] == expected, f"receipt sha mismatch for {fn}"


def test_ingest_controlled_run_cannot_enter_training_release(tmp_path: Path) -> None:
    """Even after Validator passes hypothetically, redaction NOT_APPLICABLE
    and consent missing should keep training eligibility False."""
    from app.services.claw_bakery.benchmark_ingest import ingest_benchmark_run
    rd = _write_run_dir(
        tmp_path / "runs",
        run_id="rar-test-traingate-001",
        agent_id="controlled-refund-draft-agent",
        verdict="HONEY_CANDIDATE_PENDING_VALIDATOR",
        hard_fail_count=0,
    )
    env = ingest_benchmark_run(run_dir=rd)
    assert env.pair_eligible_for_training is False


def test_safe_benchmark_metrics_no_secrets_in_payload(tmp_path: Path) -> None:
    from app.services.claw_bakery.benchmark_ingest import (
        ingest_benchmark_run,
        safe_benchmark_metrics,
    )
    rd_u = _write_run_dir(
        tmp_path / "runs",
        run_id="rar-test-metrics-unsafe",
        agent_id="unsafe-refund-agent",
        verdict="PROPOLIS",
        hard_fail_count=6,
    )
    rd_c = _write_run_dir(
        tmp_path / "runs",
        run_id="rar-test-metrics-ctrl",
        agent_id="controlled-refund-draft-agent",
        verdict="HONEY_CANDIDATE_PENDING_VALIDATOR",
        hard_fail_count=0,
    )
    ingest_benchmark_run(run_dir=rd_u)
    ingest_benchmark_run(run_dir=rd_c)
    m = safe_benchmark_metrics()
    assert m["benchmark_runs_total"] == 2
    assert m["propolis_denied_runs"] == 1
    assert m["candidate_runs_pending_validator"] == 1
    # No raw artifact bodies / prompts in the metrics payload
    blob = repr(m)
    assert "process_refund" not in blob
    assert "issue_refund" not in blob
    assert "DOCTRINE" not in blob.upper() or "controlled_demonstration" in blob


# ─── Regression · risk-doctrine fixtures still correct ──────────────


def test_swarmscout_still_elevated() -> None:
    from app.services.claw_swarm import fixtures
    from app.services.claw_swarm.risk import evaluate_intake
    from app.services.claw_swarm.structured_intake import derive_structured_intake
    fx = fixtures.SWARMSCOUT_V0_1
    si = derive_structured_intake(
        agent_name=fx["agent_name"], worker_kind=fx["worker_kind"],
        deployment_target=fx["deployment_target"], model_provider=fx["model_provider"],
        memory_enabled=fx["memory_enabled"], access_surfaces=fx["access_surfaces"],
        operator_attested_context=fx["operator_attested_context"])
    r = evaluate_intake(si)
    assert r["tier"] == "ELEVATED"
    assert r["rule_id"] == "ELEVATED_BUSINESS_DATA_AND_DRAFTING_EXPOSURE"


def test_refundranger_still_high_financial() -> None:
    from app.services.claw_swarm import fixtures
    from app.services.claw_swarm.risk import evaluate_intake
    from app.services.claw_swarm.structured_intake import derive_structured_intake
    fx = fixtures.REFUNDRANGER_V0_1
    si = derive_structured_intake(
        agent_name=fx["agent_name"], worker_kind=fx["worker_kind"],
        deployment_target=fx["deployment_target"], model_provider=fx["model_provider"],
        memory_enabled=fx["memory_enabled"], access_surfaces=fx["access_surfaces"],
        operator_attested_context=fx["operator_attested_context"])
    r = evaluate_intake(si)
    assert r["tier"] == "HIGH"
    assert r["rule_id"] == "HIGH_FINANCIAL_AUTONOMOUS_ACTION"
    blob = (r["reason"] + " " + " ".join(r["evidence_cited"])).lower()
    assert "shell" not in blob


def test_rootclaw_still_high_privileged() -> None:
    from app.services.claw_swarm import fixtures
    from app.services.claw_swarm.risk import evaluate_intake
    from app.services.claw_swarm.structured_intake import derive_structured_intake
    fx = fixtures.ROOTCLAW_V0_1
    si = derive_structured_intake(
        agent_name=fx["agent_name"], worker_kind=fx["worker_kind"],
        deployment_target=fx["deployment_target"], model_provider=fx["model_provider"],
        memory_enabled=fx["memory_enabled"], access_surfaces=fx["access_surfaces"],
        operator_attested_context=fx["operator_attested_context"])
    r = evaluate_intake(si)
    assert r["tier"] == "HIGH"
    assert r["rule_id"] == "HIGH_PRIVILEGED_OPERATIONS_COMPROMISE"
    blob = (r["reason"] + " " + " ".join(r["evidence_cited"])).lower()
    assert "payment" not in blob
