"""Claw Bakery test suite · 25 tests covering:

  Risk-engine evidence-specific rules (9)
  Pair Factory + Tribunal labels (6)
  Storage immutability + receipts (5)
  Redaction (3)
  ClawForge defaults + dataset release gating (2)

Tests run against a tmp-dir LocalDriver · no network · no DB needed.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

# Force local storage driver before any bakery import resolves the singleton
@pytest.fixture(autouse=True)
def _bakery_tmp(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("CLAW_BAKERY_STORAGE_DRIVER", "local")
    monkeypatch.setenv("CLAW_BAKERY_LOCAL_ROOT", str(tmp_path / "bakery"))
    monkeypatch.setenv("CLAW_BAKERY_CLAWFORGE_ENABLED", "false")
    # Reset the singleton so each test gets a fresh tmp store
    from app.services.claw_bakery import bakery_storage
    bakery_storage._store = None  # noqa: SLF001
    yield
    bakery_storage._store = None  # noqa: SLF001


# The autouse fixture above must run before any import that resolves the
# bakery_storage singleton, so these imports intentionally sit below it.
from app.services.claw_swarm import fixtures  # noqa: E402
from app.services.claw_swarm.risk import evaluate_intake  # noqa: E402
from app.services.claw_swarm.structured_intake import derive_structured_intake  # noqa: E402


def _eval_fixture(name: str) -> dict:
    fx = fixtures.ALL_FIXTURES[name]
    si = derive_structured_intake(
        agent_name=fx["agent_name"],
        worker_kind=fx["worker_kind"],
        deployment_target=fx["deployment_target"],
        model_provider=fx["model_provider"],
        memory_enabled=fx["memory_enabled"],
        access_surfaces=fx["access_surfaces"],
        operator_attested_context=fx["operator_attested_context"],
    )
    return evaluate_intake(si)


# ─── (1) Risk-engine evidence-specific rules ─────────────────────────


def test_swarmscout_scores_elevated() -> None:
    r = _eval_fixture("swarmscout_v0_1")
    assert r["tier"] == "ELEVATED"


def test_refundranger_scores_high() -> None:
    r = _eval_fixture("refundranger_v0_1")
    assert r["tier"] == "HIGH"


def test_rootclaw_scores_high() -> None:
    r = _eval_fixture("rootclaw_v0_1")
    assert r["tier"] == "HIGH"


def test_refundranger_rule_id_is_high_financial_autonomous_action() -> None:
    r = _eval_fixture("refundranger_v0_1")
    assert r["rule_id"] == "HIGH_FINANCIAL_AUTONOMOUS_ACTION"


def test_rootclaw_rule_id_is_high_privileged_operations_compromise() -> None:
    r = _eval_fixture("rootclaw_v0_1")
    assert r["rule_id"] == "HIGH_PRIVILEGED_OPERATIONS_COMPROMISE"


def test_rootclaw_finding_does_not_mention_payments() -> None:
    """The original v1 rule used a generic 'Shell or Payments + outbound'
    line that wrongly cited Payments for RootClaw. v2 must not."""
    r = _eval_fixture("rootclaw_v0_1")
    blob = (r["reason"] + " " + " ".join(r["evidence_cited"])).lower()
    assert "payment" not in blob, (
        f"RootClaw reason/evidence must not mention Payments · got: "
        f"reason={r['reason']!r} evidence={r['evidence_cited']!r}"
    )


def test_refundranger_finding_does_not_mention_shell() -> None:
    """RefundRanger has no shell access · reason must not cite Shell."""
    r = _eval_fixture("refundranger_v0_1")
    blob = (r["reason"] + " " + " ".join(r["evidence_cited"])).lower()
    assert "shell" not in blob, (
        f"RefundRanger reason/evidence must not mention Shell · got: "
        f"reason={r['reason']!r} evidence={r['evidence_cited']!r}"
    )


def test_high_returns_restricted_pending_controls() -> None:
    for name in ("refundranger_v0_1", "rootclaw_v0_1"):
        r = _eval_fixture(name)
        assert r["deployment_status"] == "RESTRICTED_PENDING_CONTROLS"


def test_high_returns_not_yet_eligible_for_deed_issuance() -> None:
    for name in ("refundranger_v0_1", "rootclaw_v0_1"):
        r = _eval_fixture(name)
        assert r["deed_eligibility"] == "NOT_YET_ELIGIBLE"


# ─── (2) Pair Factory + Tribunal labels ──────────────────────────────


def _make_snapshot(fixture_key: str) -> dict:
    fx = fixtures.ALL_FIXTURES[fixture_key]
    si = derive_structured_intake(
        agent_name=fx["agent_name"],
        worker_kind=fx["worker_kind"],
        deployment_target=fx["deployment_target"],
        model_provider=fx["model_provider"],
        memory_enabled=fx["memory_enabled"],
        access_surfaces=fx["access_surfaces"],
        operator_attested_context=fx["operator_attested_context"],
    )
    risk = evaluate_intake(si)
    return {
        "captured": {
            "agent_name": fx["agent_name"],
            "worker_kind": fx["worker_kind"],
            "deployment_target": fx["deployment_target"],
            "model_provider": fx["model_provider"],
            "memory_enabled": fx["memory_enabled"],
            "access_surfaces": fx["access_surfaces"],
        },
        "structured_intake": si.to_dict(),
        "risk": risk,
        "snapshot_kind": "CLAW_EXPOSURE_SNAPSHOT",
    }


def test_completed_snapshot_creates_pending_pair_candidate() -> None:
    from app.services.claw_bakery.pair_factory import (
        TribunalLabel,
        create_pair_candidate_from_snapshot,
    )
    snap = _make_snapshot("refundranger_v0_1")
    pair = create_pair_candidate_from_snapshot(
        source_run_id="cc_run_test_001",
        snapshot=snap,
        input_record_key=None,
        raw_snapshot_key="claw-bakery/raw-evidence/snapshots/cc_run_test_001.json",
        operator_consent={"allow_deidentified_training_use": False},
    )
    assert pair.tribunal_label == TribunalLabel.PENDING.value
    assert pair.synthetic is False
    assert pair.source_type == "live_intake"
    assert pair.eligible_for_training is False
    assert pair.eligible_for_evaluation is False
    assert pair.risk_class == "HIGH_FINANCIAL_AUTONOMOUS_ACTION"


def test_live_intake_not_training_eligible_without_consent() -> None:
    from app.services.claw_bakery.pair_factory import (
        RedactionStatus,
        TribunalLabel,
        ValidatorStatus,
        assign_tribunal_label,
        create_pair_candidate_from_snapshot,
        set_redaction_status,
        set_validator_status,
    )
    snap = _make_snapshot("swarmscout_v0_1")
    pair = create_pair_candidate_from_snapshot(
        source_run_id="cc_run_test_002",
        snapshot=snap,
        input_record_key=None,
        raw_snapshot_key=None,
        operator_consent={"allow_deidentified_training_use": False},
    )
    set_validator_status(pair, status=ValidatorStatus.PASSED, reason="test")
    set_redaction_status(pair, status=RedactionStatus.COMPLETED, reason="test")
    assign_tribunal_label(pair, label=TribunalLabel.HONEY, reason="test")
    assert pair.eligible_for_training is False  # consent missing


def test_live_intake_not_training_eligible_without_redaction() -> None:
    from app.services.claw_bakery.pair_factory import (
        TribunalLabel,
        ValidatorStatus,
        assign_tribunal_label,
        create_pair_candidate_from_snapshot,
        set_validator_status,
    )
    snap = _make_snapshot("swarmscout_v0_1")
    pair = create_pair_candidate_from_snapshot(
        source_run_id="cc_run_test_003",
        snapshot=snap,
        input_record_key=None,
        raw_snapshot_key=None,
        operator_consent={"allow_deidentified_training_use": True},
    )
    set_validator_status(pair, status=ValidatorStatus.PASSED, reason="test")
    assign_tribunal_label(pair, label=TribunalLabel.HONEY, reason="test")
    assert pair.eligible_for_training is False  # redaction missing


def test_synthetic_candidate_is_marked_synthetic_and_pending() -> None:
    from app.services.claw_bakery.pair_factory import (
        TribunalLabel,
        create_synthetic_candidate,
    )
    pair = create_synthetic_candidate(
        source_run_id="clawforge_test_001",
        agent_name="Synthetic Refund Agent",
        domain="refund_agent",
        risk_class="HIGH_FINANCIAL_AUTONOMOUS_ACTION",
        proposed_input={"kind": "refund_amount_injection"},
        proposed_target={"expected_action": "REFUSE"},
    )
    assert pair.synthetic is True
    assert pair.source_type == "synthetic_forge"
    assert pair.tribunal_label == TribunalLabel.PENDING.value
    assert pair.eligible_for_training is False
    assert pair.eligible_for_evaluation is False


def test_propolis_cannot_be_marked_positive_training_output() -> None:
    from app.services.claw_bakery.pair_factory import (
        PairFactoryError,
        RedactionStatus,
        TribunalLabel,
        ValidatorStatus,
        assert_can_enter_training_release,
        assign_tribunal_label,
        create_pair_candidate_from_snapshot,
        set_redaction_status,
        set_validator_status,
    )
    snap = _make_snapshot("rootclaw_v0_1")
    pair = create_pair_candidate_from_snapshot(
        source_run_id="cc_run_test_004",
        snapshot=snap,
        input_record_key=None,
        raw_snapshot_key=None,
        operator_consent={"allow_deidentified_training_use": True},
    )
    set_validator_status(pair, status=ValidatorStatus.PASSED, reason="test")
    set_redaction_status(pair, status=RedactionStatus.COMPLETED, reason="test")
    assign_tribunal_label(pair, label=TribunalLabel.PROPOLIS, reason="invented evidence")
    # Cannot flip to HONEY
    with pytest.raises(PairFactoryError):
        assign_tribunal_label(pair, label=TribunalLabel.HONEY, reason="cheating")
    # Cannot enter training release
    assert pair.eligible_for_training is False
    with pytest.raises(PairFactoryError):
        assert_can_enter_training_release(pair)


def test_holdout_seal_blocks_training_admission() -> None:
    from app.services.claw_bakery.pair_factory import (
        PairFactoryError,
        RedactionStatus,
        TribunalLabel,
        ValidatorStatus,
        assert_can_enter_training_release,
        assign_tribunal_label,
        create_pair_candidate_from_snapshot,
        seal_as_holdout,
        set_redaction_status,
        set_validator_status,
    )
    snap = _make_snapshot("swarmscout_v0_1")
    pair = create_pair_candidate_from_snapshot(
        source_run_id="cc_run_test_005",
        snapshot=snap,
        input_record_key=None,
        raw_snapshot_key=None,
        operator_consent={"allow_deidentified_training_use": True},
    )
    set_validator_status(pair, status=ValidatorStatus.PASSED, reason="test")
    set_redaction_status(pair, status=RedactionStatus.COMPLETED, reason="test")
    assign_tribunal_label(pair, label=TribunalLabel.HONEY, reason="test")
    seal_as_holdout(pair, reason="reserved for eval contamination test")
    assert pair.eligible_for_holdout is True
    assert pair.eligible_for_training is False
    with pytest.raises(PairFactoryError):
        assert_can_enter_training_release(pair)


# ─── (3) Storage immutability + receipts ─────────────────────────────


def test_raw_evidence_separate_from_derived_redacted_record() -> None:
    from app.services.claw_bakery.bakery_storage import get_bakery_store
    store = get_bakery_store()
    store.put_raw_intake("run_001", {"hello": "world"})
    store.put_redacted_for_evaluation("run_001", {"hello": "[REDACTED]"})
    raw_keys = store.list_under("raw-evidence/intakes")
    red_keys = store.list_under("redacted/approved-for-evaluation")
    assert len(raw_keys) == 1
    assert len(red_keys) == 1
    assert raw_keys[0] != red_keys[0]
    # Reading the raw artifact returns the raw payload verbatim
    raw = store.read_json(raw_keys[0])
    red = store.read_json(red_keys[0])
    assert raw["hello"] == "world"
    assert red["hello"] == "[REDACTED]"


def test_raw_evidence_write_is_immutable() -> None:
    from app.services.claw_bakery.bakery_storage import (
        KeyExistsError,
        get_bakery_store,
    )
    store = get_bakery_store()
    store.put_raw_intake("run_002", {"hello": "world"})
    with pytest.raises(KeyExistsError):
        store.put_raw_intake("run_002", {"hello": "tampered"})


def test_sha256_receipt_is_deterministic_for_stored_artifact() -> None:
    from app.services.claw_bakery.bakery_storage import get_bakery_store
    from app.services.claw_bakery.receipts import generate_receipt
    store = get_bakery_store()
    artifact = store.put_raw_intake("run_003", {"payload": [1, 2, 3]})
    body = store.driver.read(artifact.key)
    expected = hashlib.sha256(body).hexdigest()
    receipt = generate_receipt(
        artifact_type="intake",
        artifact_key=artifact.key,
        artifact_bytes=body,
        source_run_id="run_003",
    )
    assert receipt["sha256"] == expected
    # Re-running yields the same artifact hash (receipt id differs but content sha matches)
    receipt2 = generate_receipt(
        artifact_type="intake",
        artifact_key=artifact.key,
        artifact_bytes=body,
        source_run_id="run_003",
    )
    assert receipt2["sha256"] == expected


def test_safe_public_metrics_exposes_only_aggregates() -> None:
    from app.services.claw_bakery.bakery_storage import get_bakery_store
    from app.services.claw_bakery.ingest import safe_public_metrics
    store = get_bakery_store()
    store.put_raw_intake("run_pub_001", {"secret_field": "do_not_expose"})
    m = safe_public_metrics(store=store)
    # The aggregate counters must be present
    for key in (
        "intakes_captured", "snapshots_generated", "pending_pair_candidates",
        "honey_pair_candidates", "receipts_hashed", "dataset_releases",
        "events_recorded", "benchmark_lanes",
    ):
        assert key in m
    # No artifact body is leaked
    assert "secret_field" not in repr(m)


def test_event_outbox_writes_immutable_envelope() -> None:
    from app.services.claw_bakery.bakery_events import append_event, list_events
    env = append_event(
        event_type="clawcheck.intake.completed",
        run_id="run_outbox_001",
        payload={"intake_complete": True},
    )
    assert env["event_type"] == "clawcheck.intake.completed"
    assert env["sha256"]
    keys = list_events()
    assert any(env["event_id"] in k for k in keys)


# ─── (4) Redaction ───────────────────────────────────────────────────


def test_redaction_scrubs_email_phone_address_credit_token_envkv() -> None:
    from app.services.claw_bakery.redaction import redact_text
    text = (
        "Contact j.doe@example.com or call +1 (212) 555-0142. "
        "Ship to 1600 Pennsylvania Avenue. "
        "Card 4111 1111 1111 1111 OPENAI_API_KEY=sk-abcdefghijklmnopqrstuv0123 "
        "GITHUB_TOKEN=ghp_aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    )
    r = redact_text(text)
    out = r.redacted_text.lower()
    assert "[redacted_email]" in out
    assert "[redacted_phone]" in out
    assert "[redacted_address]" in out
    assert "[redacted_pan]" in out or "[redacted_token]" in out
    assert r.hits.get("email", 0) >= 1


def test_redaction_assert_raises_on_residual_pii() -> None:
    from app.services.claw_bakery.redaction import (
        RedactionRefusal,
        assert_redacted,
        redact_text,
    )
    # Pre-construct a bad result manually to verify the assertion gate.
    r = redact_text("clean text")
    assert_redacted(r)  # does not raise
    r.clean_after_scrub = False
    with pytest.raises(RedactionRefusal):
        assert_redacted(r)


def test_redaction_operator_named_pii_is_replaced() -> None:
    from app.services.claw_bakery.redaction import redact_text
    r = redact_text("Hello Frances", operator_named_pii=["Frances"])
    assert "Frances" not in r.redacted_text
    assert "[REDACTED_NAME]" in r.redacted_text


# ─── (5) ClawForge + dataset release gating ─────────────────────────


def test_clawforge_disabled_by_default_refuses_generation() -> None:
    from app.services.claw_bakery.clawforge import generate_synthetic_candidate
    with pytest.raises(RuntimeError):
        generate_synthetic_candidate(template_index=0)


def test_draft_dataset_release_excludes_holdouts_and_unconsented() -> None:
    from app.services.claw_bakery.dataset_release import build_draft_release
    from app.services.claw_bakery.pair_factory import (
        RedactionStatus,
        TribunalLabel,
        ValidatorStatus,
        assign_tribunal_label,
        create_pair_candidate_from_snapshot,
        seal_as_holdout,
        set_redaction_status,
        set_validator_status,
    )
    snap = _make_snapshot("swarmscout_v0_1")
    # A · approvable
    approvable = create_pair_candidate_from_snapshot(
        source_run_id="cc_run_rel_001",
        snapshot=snap,
        input_record_key=None,
        raw_snapshot_key=None,
        operator_consent={"allow_deidentified_training_use": True},
    )
    set_validator_status(approvable, status=ValidatorStatus.PASSED, reason="ok")
    set_redaction_status(approvable, status=RedactionStatus.COMPLETED, reason="ok")
    assign_tribunal_label(approvable, label=TribunalLabel.HONEY, reason="ok")
    # B · holdout (must be excluded)
    holdout = create_pair_candidate_from_snapshot(
        source_run_id="cc_run_rel_002",
        snapshot=snap,
        input_record_key=None,
        raw_snapshot_key=None,
        operator_consent={"allow_deidentified_training_use": True},
    )
    set_validator_status(holdout, status=ValidatorStatus.PASSED, reason="ok")
    set_redaction_status(holdout, status=RedactionStatus.COMPLETED, reason="ok")
    assign_tribunal_label(holdout, label=TribunalLabel.HONEY, reason="ok")
    seal_as_holdout(holdout, reason="reserved")
    # C · unconsented (must be refused)
    unconsented = create_pair_candidate_from_snapshot(
        source_run_id="cc_run_rel_003",
        snapshot=snap,
        input_record_key=None,
        raw_snapshot_key=None,
        operator_consent={"allow_deidentified_training_use": False},
    )
    set_validator_status(unconsented, status=ValidatorStatus.PASSED, reason="ok")
    set_redaction_status(unconsented, status=RedactionStatus.COMPLETED, reason="ok")
    assign_tribunal_label(unconsented, label=TribunalLabel.HONEY, reason="ok")
    rel = build_draft_release(
        dataset_id="DEFENDABLE-CLAWCHECK-TRIBUNAL-V1",
        version="0.1.0-test",
        pair_candidates=[approvable, holdout, unconsented],
    )
    assert rel["status"] == "DRAFT"
    assert rel["pair_counts"]["honey"] == 1
    assert holdout.pair_id in rel["excluded_holdouts"]
    refused_ids = {r["pair_id"] for r in rel["refused_with_reason"]}
    assert unconsented.pair_id in refused_ids
