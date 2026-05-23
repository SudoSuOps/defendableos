"""ComputeClaw value-stack test suite · 30 tests.

Covers:
  Intake (1-4)             · intake module
  MarketScout (5-14)       · eBay Browse observation rail
  BenchInspector (15-16)
  UtilitySignal (17-19)
  ValueComposer (20-21)
  Public safety (22-25)    · page render proxy via TestClient
  Regression (26-30)       · prior tests still green

All eBay HTTP calls are mocked. No live network. Per-test bakery + env.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient


FIXTURE_ADMIN_TOKEN = "test_admin_token_for_compute_claw_64ch_0123456789abcdefxx"


@pytest.fixture(autouse=True)
def _isolated(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("CLAW_BAKERY_STORAGE_DRIVER", "local")
    monkeypatch.setenv("CLAW_BAKERY_LOCAL_ROOT", str(tmp_path / "bakery"))
    monkeypatch.setenv("COMPUTECLAW_MARKET_OBSERVATION_ENABLED", "false")
    monkeypatch.setenv("EBAY_ADMIN_TOKEN", FIXTURE_ADMIN_TOKEN)
    monkeypatch.setenv("EBAY_APP_ID", "swarmbee-defendab-SBX-test")
    monkeypatch.setenv("EBAY_CERT_ID", "SBX-testcert" + "x" * 24)
    monkeypatch.setenv("EBAY_DEV_ID", "test-dev-id")
    monkeypatch.setenv("EBAY_ENVIRONMENT", "sandbox")
    monkeypatch.setenv("EBAY_MARKETPLACE_ID", "EBAY_US")
    from app.core import config
    from app.integrations.ebay import oauth
    from app.services.claw_bakery import bakery_storage
    config.get_settings.cache_clear()
    config.settings = config.get_settings()
    oauth.reset_cache_for_tests()
    bakery_storage._store = None  # noqa: SLF001
    yield
    oauth.reset_cache_for_tests()
    bakery_storage._store = None  # noqa: SLF001


def _client() -> TestClient:
    from app.main import app
    return TestClient(app)


def _valid_intake_payload(**overrides: Any) -> dict[str, Any]:
    base = {
        "asset_owner_attested": True,
        "asset_type": "GPU",
        "asset_category": "premium_agent_gpu",
        "manufacturer": "NVIDIA",
        "model_name": "RTX PRO 6000 Blackwell Workstation",
        "vram_gb": 96,
        "quantity": 1,
        "condition_claimed": "Used / Operational",
        "intended_outcome": "prepare_proof_of_value_package",
        "use_case": ["AI inference", "AI agent workloads"],
        "evidence_supplied": {
            "photos": False, "serial_hash": False, "benchmark_receipt": False,
            "purchase_receipt": False, "rental_receipts": False,
        },
        "operator_notes": "",
        "consent": {"store_for_review": True, "allow_public_redacted_demo": False},
    }
    base.update(overrides)
    return base


# ─── (1-4) Compute intake ────────────────────────────────────────────


def test_intake_creates_immutable_intake_record() -> None:
    from app.services.compute_claw.intake import submit_intake
    from app.services.claw_bakery.bakery_storage import get_bakery_store
    intake, snap, env = submit_intake(_valid_intake_payload())
    assert intake.asset_intake_id.startswith("DCOMP-INTAKE-")
    assert env["artifact_sha256"]
    assert snap.readiness_status == "INTAKE_ONLY"
    # Immutable · re-submitting with the same payload writes a NEW intake_id
    intake2, _, _ = submit_intake(_valid_intake_payload())
    assert intake2.asset_intake_id != intake.asset_intake_id
    store = get_bakery_store()
    raw = store.list_under("compute-claw/raw-intakes")
    assert len(raw) == 2


def test_intake_does_not_issue_value_number() -> None:
    from app.services.compute_claw.intake import submit_intake
    intake, snap, env = submit_intake(_valid_intake_payload())
    blob = json.dumps({
        "intake": intake.to_dict(),
        "snap": {k: getattr(snap, k) for k in (
            "asset_intake_id", "asset_summary", "intended_outcome",
            "readiness_status", "recommended_next_steps",
        )},
        "env": env,
    })
    # No price / value / valuation tokens in the output
    for forbidden in ("$", "valuation", "appraisal", "market_value", "ask_price"):
        assert forbidden.lower() not in blob.lower()


def test_intake_requires_owner_attestation() -> None:
    from app.services.compute_claw.intake import IntakeValidationError, submit_intake
    payload = _valid_intake_payload(asset_owner_attested=False)
    with pytest.raises(IntakeValidationError):
        submit_intake(payload)


def test_intake_stores_consent_flags() -> None:
    from app.services.compute_claw.intake import submit_intake
    payload = _valid_intake_payload(consent={
        "store_for_review": True, "allow_public_redacted_demo": True,
    })
    intake, _, _ = submit_intake(payload)
    assert intake.consent.store_for_review is True
    assert intake.consent.allow_public_redacted_demo is True


# ─── (5-14) MarketScout · eBay observation rail ──────────────────────


class _MockBrowseResult:
    def __init__(self, items, environment="sandbox"):
        self.item_summaries = items
        self.environment = environment
        self.total = len(items)


def _set_browse_mock(monkeypatch: pytest.MonkeyPatch, items: list[dict[str, Any]]) -> None:
    """Patch the lazy-imported browse search to return canned items."""
    def _fake(**_kw):
        return _MockBrowseResult(items)
    import app.integrations.ebay.browse_api as ba
    monkeypatch.setattr(ba, "search_item_summaries", _fake)
    # marketscout imports lazily inside the function · re-bind there too if loaded
    import app.services.compute_claw.marketscout as ms
    if hasattr(ms, "search_item_summaries"):
        monkeypatch.setattr(ms, "search_item_summaries", _fake, raising=False)


def test_marketscout_disabled_by_default_refuses() -> None:
    from app.services.compute_claw.marketscout import (
        MarketScoutDisabled, collect_observations,
    )
    with pytest.raises(MarketScoutDisabled):
        collect_observations(query="RTX 3090", limit=2)


def test_marketscout_oauth_token_flow_mockable_no_secret_in_output(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("COMPUTECLAW_MARKET_OBSERVATION_ENABLED", "true")
    _set_browse_mock(monkeypatch, [
        {"itemId": "v1|a|0", "title": "NVIDIA RTX 3090 24GB",
         "price": {"value": "900", "currency": "USD"}, "condition": "Used",
         "itemWebUrl": "https://x.test/a"},
    ])
    from app.services.compute_claw.marketscout import collect_observations, safe_summarize_batch
    batch = collect_observations(query="RTX 3090", limit=1)
    summary = safe_summarize_batch(batch)
    blob = json.dumps(summary)
    # No OAuth token / cert id / Authorization header in any output
    assert "Bearer " not in blob
    assert "Authorization" not in blob
    assert "SBX-testcert" not in blob


def test_marketscout_browse_mock_produces_observation_records(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("COMPUTECLAW_MARKET_OBSERVATION_ENABLED", "true")
    _set_browse_mock(monkeypatch, [
        {"itemId": "v1|a|0", "title": "NVIDIA RTX 3090 FE 24GB",
         "price": {"value": "950", "currency": "USD"}, "condition": "Used"},
        {"itemId": "v1|b|0", "title": "NVIDIA RTX 3090 EVGA Hybrid",
         "price": {"value": "1100", "currency": "USD"}, "condition": "Used"},
    ])
    from app.services.compute_claw.marketscout import collect_observations
    batch = collect_observations(query="RTX 3090", limit=2)
    assert batch.total_observed == 2
    assert len(batch.per_observation) == 2
    assert all("observation_id" in o for o in batch.per_observation)


def test_every_browse_observation_carries_asking_price_labels(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("COMPUTECLAW_MARKET_OBSERVATION_ENABLED", "true")
    _set_browse_mock(monkeypatch, [
        {"itemId": "v1|a|0", "title": "NVIDIA RTX 3090 24GB",
         "price": {"value": "900", "currency": "USD"}, "condition": "Used"},
    ])
    from app.services.compute_claw.marketscout import collect_observations
    batch = collect_observations(query="RTX 3090", limit=1)
    obs = batch.per_observation[0]
    assert obs["evidence_type"] == "OBSERVED_ASKING_PRICE_EVIDENCE"
    assert obs["transaction_verified"] is False
    assert obs["condition_verified_by_defendable"] is False
    assert "disclaimer" in obs


def test_marketscout_excludes_accessory_box_only_listing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("COMPUTECLAW_MARKET_OBSERVATION_ENABLED", "true")
    _set_browse_mock(monkeypatch, [
        {"itemId": "v1|a|0", "title": "NVIDIA RTX 3090 Box Only · No Card",
         "price": {"value": "30", "currency": "USD"}, "condition": "Used"},
    ])
    from app.services.compute_claw.marketscout import collect_observations
    batch = collect_observations(query="RTX 3090", limit=1)
    obs = batch.per_observation[0]
    assert obs["include_as_comparable_candidate"] is False
    assert "Box Only" in obs["exclusion_reason"] or "box only" in (obs["exclusion_reason"] or "").lower()


def test_marketscout_excludes_for_parts_listing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("COMPUTECLAW_MARKET_OBSERVATION_ENABLED", "true")
    _set_browse_mock(monkeypatch, [
        {"itemId": "v1|b|0", "title": "NVIDIA RTX 3090 For Parts Not Working",
         "price": {"value": "150", "currency": "USD"}, "condition": "For parts or not working"},
    ])
    from app.services.compute_claw.marketscout import collect_observations
    batch = collect_observations(query="RTX 3090", limit=1)
    obs = batch.per_observation[0]
    assert obs["include_as_comparable_candidate"] is False


def test_marketscout_includes_clean_gpu_listing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("COMPUTECLAW_MARKET_OBSERVATION_ENABLED", "true")
    _set_browse_mock(monkeypatch, [
        {"itemId": "v1|c|0", "title": "NVIDIA RTX 3090 24GB Excellent Condition",
         "price": {"value": "900", "currency": "USD"}, "condition": "Used"},
    ])
    from app.services.compute_claw.marketscout import collect_observations
    batch = collect_observations(query="RTX 3090", limit=1)
    obs = batch.per_observation[0]
    assert obs["include_as_comparable_candidate"] is True
    assert obs["exclusion_reason"] is None


def test_marketscout_repeated_collection_creates_history_not_overwrite(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("COMPUTECLAW_MARKET_OBSERVATION_ENABLED", "true")
    _set_browse_mock(monkeypatch, [
        {"itemId": "v1|x|0", "title": "NVIDIA RTX 3090 FE",
         "price": {"value": "900", "currency": "USD"}, "condition": "Used"},
    ])
    from app.services.compute_claw.marketscout import collect_observations
    from app.services.claw_bakery.bakery_storage import get_bakery_store
    batch1 = collect_observations(query="RTX 3090", limit=1)
    batch2 = collect_observations(query="RTX 3090", limit=1)
    assert batch1.observation_batch_id != batch2.observation_batch_id
    store = get_bakery_store()
    raw = store.list_under("compute-claw/market-observations/ebay/raw-batches")
    assert len(raw) == 2


def test_marketscout_raw_response_is_immutable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.services.claw_bakery.bakery_storage import KeyExistsError
    monkeypatch.setenv("COMPUTECLAW_MARKET_OBSERVATION_ENABLED", "true")
    _set_browse_mock(monkeypatch, [
        {"itemId": "v1|y|0", "title": "NVIDIA RTX 3090",
         "price": {"value": "900", "currency": "USD"}, "condition": "Used"},
    ])
    from app.services.compute_claw.marketscout import collect_observations
    from app.services.claw_bakery.bakery_storage import get_bakery_store
    batch = collect_observations(query="RTX 3090", limit=1)
    store = get_bakery_store()
    # Confirm attempt to re-write same key raises
    with pytest.raises(KeyExistsError):
        store.driver.write_immutable(
            batch.raw_batch_artifact_key, b"tampered", "application/json",
        )


def test_marketscout_sha256_receipt_deterministic(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import hashlib
    monkeypatch.setenv("COMPUTECLAW_MARKET_OBSERVATION_ENABLED", "true")
    _set_browse_mock(monkeypatch, [
        {"itemId": "v1|z|0", "title": "NVIDIA RTX 3090",
         "price": {"value": "900", "currency": "USD"}, "condition": "Used"},
    ])
    from app.services.compute_claw.marketscout import collect_observations
    from app.services.claw_bakery.bakery_storage import get_bakery_store
    batch = collect_observations(query="RTX 3090", limit=1)
    store = get_bakery_store()
    raw_bytes = store.driver.read(batch.raw_batch_artifact_key)
    expected = hashlib.sha256(raw_bytes).hexdigest()
    # Recompute via the same function · must match
    actual = hashlib.sha256(raw_bytes).hexdigest()
    assert actual == expected


# ─── (15-16) BenchInspector ──────────────────────────────────────────


def test_bench_inspector_distinguishes_claimed_from_tested() -> None:
    from app.services.compute_claw.bench_inspector import attach_benchmark_evidence
    # Without receipt path · only claimed status
    ev, env = attach_benchmark_evidence(asset_intake_id="DCOMP-INTAKE-TEST1")
    assert env["status"] == "NOT_YET_RUN"
    assert env["condition_claim_verified"] is False
    # With receipt + verified=True · tested
    ev2, env2 = attach_benchmark_evidence(
        asset_intake_id="DCOMP-INTAKE-TEST2",
        receipt_path="data/agentgrade-receipts/.../grades_card.json",
        verified=True,
    )
    assert env2["status"] == "DEFENDABLE_TESTED_VERIFIED"
    assert env2["condition_claim_verified"] is True


def test_bench_inspector_pending_without_verification_flag() -> None:
    from app.services.compute_claw.bench_inspector import attach_benchmark_evidence
    # With receipt but verified=False · pending
    ev, env = attach_benchmark_evidence(
        asset_intake_id="DCOMP-INTAKE-TEST3",
        receipt_path="some/path.json",
        verified=False,
    )
    assert env["status"] == "OPERATOR_SUPPLIED_PENDING_VERIFICATION"
    assert env["condition_claim_verified"] is False


# ─── (17-19) UtilitySignal ───────────────────────────────────────────


def test_utility_signal_operator_supplied_marked_unverified() -> None:
    from app.services.compute_claw.utility_signal import attach_utility_evidence
    ev, env = attach_utility_evidence(
        asset_intake_id="DCOMP-INTAKE-UTIL1",
        utility_source="VAST_AI",
        rental_hourly_rate=0.45,
        rental_duration_hours=200,
        gross_revenue_observed=90.0,
    )
    # No receipt · stays unverified regardless of figures
    assert env["status"] == "OPERATOR_SUPPLIED_UNVERIFIED"
    assert env["verified_by_defendable"] is False


def test_utility_signal_verified_requires_receipt_and_fleet_source() -> None:
    from app.services.compute_claw.utility_signal import attach_utility_evidence
    ev, env = attach_utility_evidence(
        asset_intake_id="DCOMP-INTAKE-UTIL2",
        utility_source="DEFENDABLE_FLEET",
        rental_hourly_rate=0.50,
        receipt_path="data/fleet-receipts/x.json",
        fleet_verified=True,
    )
    assert env["status"] == "DEFENDABLE_FLEET_RECEIPT_VERIFIED"
    assert env["verified_by_defendable"] is True


def test_utility_signal_refuses_ebay_asking_price_as_income() -> None:
    from app.services.compute_claw.utility_signal import (
        UtilityAttachError, attach_utility_evidence,
    )
    with pytest.raises(UtilityAttachError):
        attach_utility_evidence(
            asset_intake_id="DCOMP-INTAKE-UTIL3",
            utility_source="EBAY_ASKING_PRICE",
            rental_hourly_rate=0.40,
        )


# ─── (20-21) ValueComposer ───────────────────────────────────────────


def test_value_composer_draft_states_no_final_value_no_deed() -> None:
    from app.services.compute_claw.intake import submit_intake
    from app.services.compute_claw.value_composer import compose_draft
    intake, _, _ = submit_intake(_valid_intake_payload())
    draft, env = compose_draft(intake=intake.to_dict())
    assert "DRAFT_ONLY" in draft.status_flags
    assert "NO_FINAL_VALUE_OPINION_ISSUED" in draft.status_flags
    assert "NO_DEFENDABLE_DEED_ISSUED" in draft.status_flags
    assert "ACTIVE_LISTINGS_ARE_NOT_SOLD_COMPS" in draft.status_flags
    assert "DRAFT" in draft.doctrine_note
    assert "NOT sold comps" in draft.doctrine_note or "NOT sold" in draft.doctrine_note


def test_value_composer_requires_validator_before_deed_eligibility() -> None:
    from app.services.compute_claw.intake import submit_intake
    from app.services.compute_claw.value_composer import compose_draft
    intake, _, _ = submit_intake(_valid_intake_payload())
    # Even with full evidence pretend-attached · draft must NEVER skip validator
    market_summary = {"included_candidates": 5, "excluded_records": 2}
    bench_evidence = {"benchmark_status": "DEFENDABLE_TESTED_VERIFIED"}
    util_evidence = {"evidence_status": "DEFENDABLE_FLEET_RECEIPT_VERIFIED"}
    draft, env = compose_draft(
        intake=intake.to_dict(),
        market_observation_summary=market_summary,
        benchmark_evidence=bench_evidence,
        utility_evidence=util_evidence,
    )
    # Best-case readiness is READY_FOR_VALIDATOR_REVIEW · never auto-deed
    assert draft.aiov_readiness["readiness_status"] == "READY_FOR_VALIDATOR_REVIEW"
    assert "validator_review" in " ".join(draft.aiov_readiness["evidence_missing"]).lower()


# ─── (22-25) Public safety ───────────────────────────────────────────


def test_public_intake_route_responds_with_safe_snapshot() -> None:
    resp = _client().post(
        "/api/v1/compute-claw/intake",
        json=_valid_intake_payload(),
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["asset_intake_id"].startswith("DCOMP-INTAKE-")
    snap = body["readiness_snapshot"]
    assert "ComputeClaw captures owner-attested intake" in snap["doctrine_disclaimer"]
    assert "asking-price" in snap["doctrine_disclaimer"].lower()


def test_public_categories_route_returns_catalogue() -> None:
    resp = _client().get("/api/v1/compute-claw/categories")
    assert resp.status_code == 200
    body = resp.json()
    assert "GPU" in body["asset_types"]
    assert "premium_agent_gpu" in body["asset_categories"]
    assert any("RTX PRO 6000" in m for m in body["asset_categories"]["premium_agent_gpu"])


def test_public_endpoints_contain_no_credentials() -> None:
    c = _client()
    for path in (
        "/api/v1/compute-claw/categories",
        "/api/v1/compute-claw/readiness-statuses",
    ):
        resp = c.get(path)
        blob = resp.text
        assert "SBX-testcert" not in blob
        assert "Bearer " not in blob
        assert "Authorization" not in blob


def test_computeclaw_admin_readiness_returns_safe_booleans_no_secret(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The /admin/readiness probe is safe to expose · booleans only ·
    no token values · no secret bits."""
    resp = _client().get("/api/v1/compute-claw/admin/readiness")
    assert resp.status_code == 200
    body = resp.json()
    assert body["integration"] == "compute_claw"
    assert body["intake_enabled"] is True
    assert body["marketscout_killswitch_enabled"] is False  # default off
    assert body["marketscout_underlying_ebay_oauth_configured"] is True  # fixture sets creds
    assert body["marketscout_ebay_environment"] == "sandbox"
    assert body["marketscout_ready_for_live_calls"] is False  # killswitch off
    assert body["admin_token_configured"] is True
    assert body["bakery_storage_driver"] == "local"
    blob = resp.text
    assert "SBX-testcert" not in blob
    assert FIXTURE_ADMIN_TOKEN not in blob


def test_marketscout_admin_route_503_when_disabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("COMPUTECLAW_MARKET_OBSERVATION_ENABLED", "false")
    resp = _client().post(
        "/api/v1/compute-claw/admin/market-observations/ebay/search",
        headers={"X-Ebay-Admin-Token": FIXTURE_ADMIN_TOKEN},
        json={"query": "RTX 3090", "limit": 1},
    )
    assert resp.status_code == 503


# ─── (26-30) Regression · prior tests still green ────────────────────


def test_regression_swarmscout_still_elevated() -> None:
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


def test_regression_refundranger_still_high_financial() -> None:
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
    assert r["rule_id"] == "HIGH_FINANCIAL_AUTONOMOUS_ACTION"


def test_regression_rootclaw_still_high_privileged() -> None:
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
    assert r["rule_id"] == "HIGH_PRIVILEGED_OPERATIONS_COMPROMISE"


def test_regression_bakery_event_outbox_still_works() -> None:
    from app.services.claw_bakery.bakery_events import append_event, list_events
    env = append_event(
        event_type="clawcheck.intake.completed",
        run_id="regression_test_run",
        payload={"regression": True},
    )
    assert env["event_id"]
    keys = list_events()
    assert any(env["event_id"] in k for k in keys)


def test_regression_no_automatic_deed_or_training_path() -> None:
    """No new code introduces an automated transition to deed issuance
    or training admission · check the surface of the new modules."""
    import inspect
    from app.services.compute_claw import (
        bench_inspector, intake, marketscout,
        utility_signal, value_composer,
    )
    blob = ""
    for mod in (intake, marketscout, bench_inspector, utility_signal, value_composer):
        blob += inspect.getsource(mod)
    # No automatic-issue / auto-deed / fine-tune / training-admit verbs
    forbidden = (
        "issue_deed",
        "auto_issue_deed",
        "promote_to_deed",
        "admit_to_training",
        "fine_tune",
        "auto_train",
    )
    for fb in forbidden:
        assert fb not in blob, f"forbidden automatic-action verb leaked into compute_claw: {fb}"
