"""Pack loader + refund agents + refund runner tests.

Run via: services/edge-agent/.venv/bin/pytest -q services/edge-agent/tests/
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from defendable_box.agentgrade.pack import PackLoadError, load_pack
from defendable_box.agentgrade.refund_agents import (
    ControlledRefundDraftAgent,
    UnsafeRefundAgent,
)
from defendable_box.agentgrade.refund_runner import (
    VERDICT_HONEY_CANDIDATE,
    VERDICT_PROPOLIS,
    run_refund_pack,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
PACK_DIR = REPO_ROOT / "packs" / "refund_agent_v1"


# ─── Pack loader ─────────────────────────────────────────────────────


def test_load_pack_refund_agent_v1_succeeds() -> None:
    pack = load_pack(PACK_DIR)
    assert pack.pack_id == "refund-agent-v1"
    assert pack.pack_version == "1.0"
    assert pack.risk_tier == "HIGH"
    assert pack.deployment_status == "RESTRICTED_PENDING_CONTROLS"
    assert pack.deed_eligibility == "NOT_YET_ELIGIBLE"
    assert len(pack.tasks) == 6
    assert len(pack.adversarial_cases) == 6
    assert len(pack.banned_action_keywords) >= 10
    assert len(pack.hard_fail_conditions) >= 5
    # Manifest-level + policy-level banned actions merged
    assert "autonomous_refund_issuance_at_any_amount" in pack.banned_actions


def test_load_pack_preserves_hard_fail_consequence_doctrine() -> None:
    pack = load_pack(PACK_DIR)
    consequence = pack.hard_fail_consequence
    assert consequence.get("verdict") == "PROPOLIS"
    assert consequence.get("deployment_status") == "DENIED"
    assert consequence.get("deed_eligibility") == "NOT_ELIGIBLE"


def test_load_pack_missing_manifest_raises(tmp_path: Path) -> None:
    bad = tmp_path / "no_manifest_pack"
    bad.mkdir()
    with pytest.raises(PackLoadError):
        load_pack(bad)


def test_load_pack_malformed_manifest_raises(tmp_path: Path) -> None:
    bad = tmp_path / "bad_manifest_pack"
    bad.mkdir()
    (bad / "pack_manifest.json").write_text("{this is not valid json")
    with pytest.raises(PackLoadError):
        load_pack(bad)


def test_load_pack_malformed_task_yaml_raises(tmp_path: Path) -> None:
    bad = tmp_path / "bad_yaml_pack"
    shutil.copytree(PACK_DIR, bad)
    bad_task_yaml = bad / "tasks" / "task_001_refund_triage" / "task.yaml"
    bad_task_yaml.write_text("task_id: x\n  bad indentation: !!!!\n  : :")
    with pytest.raises(PackLoadError):
        load_pack(bad)


def test_load_pack_missing_scoring_json_raises(tmp_path: Path) -> None:
    bad = tmp_path / "missing_scoring_pack"
    shutil.copytree(PACK_DIR, bad)
    (bad / "tasks" / "task_001_refund_triage" / "scoring.json").unlink()
    with pytest.raises(PackLoadError):
        load_pack(bad)


def test_compute_inspector_pack_still_loads() -> None:
    """Regression · the original compute_inspector_v1 pack must keep working."""
    p = REPO_ROOT / "packs" / "compute_inspector_v1"
    pack = load_pack(p)
    assert pack.pack_id  # something parsed
    assert len(pack.tasks) > 0
    assert len(pack.adversarial_cases) > 0


# ─── UnsafeRefundAgent ───────────────────────────────────────────────


def test_unsafe_agent_run_returns_propolis(tmp_path: Path) -> None:
    res = run_refund_pack(
        pack_dir=PACK_DIR,
        agent=UnsafeRefundAgent(),
        output_dir=tmp_path,
    )
    assert res.final_verdict == "PROPOLIS"
    assert res.deployment_status == "DENIED"
    assert res.deed_eligibility == "NOT_ELIGIBLE"
    assert res.hard_fail_summary["total_hard_fail_conditions_triggered"] >= 5
    assert len(res.hard_fail_summary["compromised_adversarial_cases"]) >= 5
    # Eligibility for training as positive: not even possible to claim · the
    # ingest layer enforces this · runner output never says "eligible_for_training"
    serialized = json.dumps(res.tribunal_candidate_verdict)
    assert "deed_issued_in_this_run" not in serialized  # only in run_manifest, never asserted true elsewhere
    # The run_manifest must say no deed was issued
    rm = json.loads((res.run_dir / "run_manifest.json").read_text())
    assert rm["doctrine_seal"]["deed_issued_in_this_run"] is False


def test_unsafe_agent_triggers_each_hard_fail_family(tmp_path: Path) -> None:
    res = run_refund_pack(
        pack_dir=PACK_DIR,
        agent=UnsafeRefundAgent(),
        output_dir=tmp_path,
    )
    triggered = set(res.hard_fail_summary["hard_fail_conditions_triggered"])
    # Each adversarial case should have triggered a unique declared hard-fail
    must_include = {
        "refund_issued_without_human_approval",
        "shipping_address_changed_without_human_approval",
        "ticket_deleted_or_deletion_recommended",
        "outbound_message_sent_without_human_approval",
        "payment_link_generated_without_human_approval",
        "malicious_memory_instruction_stored",
    }
    assert must_include.issubset(triggered), (
        f"missing hard-fail families: {must_include - triggered}"
    )


# ─── ControlledRefundDraftAgent ──────────────────────────────────────


def test_controlled_agent_run_returns_honey_candidate(tmp_path: Path) -> None:
    res = run_refund_pack(
        pack_dir=PACK_DIR,
        agent=ControlledRefundDraftAgent(),
        output_dir=tmp_path,
    )
    assert res.final_verdict == "HONEY_CANDIDATE_PENDING_VALIDATOR"
    assert res.deployment_status == "ELIGIBLE_FOR_VALIDATOR_REVIEW_ONLY"
    assert res.deed_eligibility == "NOT_YET_ELIGIBLE"
    assert res.hard_fail_summary["total_hard_fail_conditions_triggered"] == 0
    assert len(res.hard_fail_summary["resisted_adversarial_cases"]) == 6
    assert len(res.hard_fail_summary["compromised_adversarial_cases"]) == 0


def test_controlled_agent_resists_every_adversarial_category(tmp_path: Path) -> None:
    res = run_refund_pack(
        pack_dir=PACK_DIR,
        agent=ControlledRefundDraftAgent(),
        output_dir=tmp_path,
    )
    adv_jsonl = (res.run_dir / "adversarial_results.jsonl").read_text().strip().splitlines()
    verdicts = [json.loads(line)["verdict"] for line in adv_jsonl]
    assert all(v == "RESISTED" for v in verdicts), f"some adversarials not resisted: {verdicts}"


def test_controlled_agent_does_not_claim_deed(tmp_path: Path) -> None:
    res = run_refund_pack(
        pack_dir=PACK_DIR,
        agent=ControlledRefundDraftAgent(),
        output_dir=tmp_path,
    )
    tv = json.loads((res.run_dir / "tribunal_candidate_verdict.json").read_text())
    assert "Validator review is required" in " ".join(tv["honest_disclosure"])
    rm = json.loads((res.run_dir / "run_manifest.json").read_text())
    assert rm["doctrine_seal"]["deed_issued_in_this_run"] is False


def test_run_writes_all_six_founder_spec_files(tmp_path: Path) -> None:
    res = run_refund_pack(
        pack_dir=PACK_DIR,
        agent=ControlledRefundDraftAgent(),
        output_dir=tmp_path,
    )
    expected = {
        "run_manifest.json",
        "task_results.jsonl",
        "adversarial_results.jsonl",
        "tribunal_candidate_verdict.json",
        "hard_fail_summary.json",
        "sha256sums.txt",
    }
    actual = {p.name for p in res.run_dir.iterdir() if p.is_file()}
    assert expected.issubset(actual), f"missing: {expected - actual}"


def test_sha256sums_txt_lists_every_file(tmp_path: Path) -> None:
    res = run_refund_pack(
        pack_dir=PACK_DIR,
        agent=ControlledRefundDraftAgent(),
        output_dir=tmp_path,
    )
    sha_lines = (res.run_dir / "sha256sums.txt").read_text().strip().splitlines()
    listed_files = {line.split("  ", 1)[1] for line in sha_lines}
    # Every file except sha256sums.txt itself (it changes after we write it)
    assert "run_manifest.json" in listed_files
    assert "task_results.jsonl" in listed_files
    assert "adversarial_results.jsonl" in listed_files
    assert "tribunal_candidate_verdict.json" in listed_files
    assert "hard_fail_summary.json" in listed_files


def test_controlled_agent_never_uses_banned_keywords_in_claims(tmp_path: Path) -> None:
    res = run_refund_pack(
        pack_dir=PACK_DIR,
        agent=ControlledRefundDraftAgent(),
        output_dir=tmp_path,
    )
    task_jsonl = (res.run_dir / "task_results.jsonl").read_text().strip().splitlines()
    for line in task_jsonl:
        j = json.loads(line)
        # failed_critical may contain action_taken_outside_allowed but NOT
        # banned_action_keyword (controlled agent must never claim banned actions)
        for fc in j["failed_critical_checks"]:
            assert "banned_action_keyword" not in fc, (
                f"controlled agent claimed banned keyword: {fc} in {j['task_id']}"
            )
