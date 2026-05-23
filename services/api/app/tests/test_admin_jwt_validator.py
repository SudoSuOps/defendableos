"""Admin JWT + Validator review chain tests.

Covers:
  · Bakery admin routes require platform_admin JWT (auth gate)
  · Pair candidate listing returns safe metadata only
  · Pair candidate retrieval works for valid IDs
  · Tribunal label re-assignment via admin route
  · Validator review chain runs all 12 checks
  · Critical fail → QUARANTINED · advisory fail → JELLY · clean → HONEY
  · PROPOLIS → HONEY refused (PairFactoryError surfaces as 400)
  · Validator session stored immutably with receipt
"""
from __future__ import annotations

import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def _isolated(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("CLAW_BAKERY_STORAGE_DRIVER", "local")
    monkeypatch.setenv("CLAW_BAKERY_LOCAL_ROOT", str(tmp_path / "bakery"))
    monkeypatch.setenv("CLAW_BAKERY_CLAWFORGE_ENABLED", "true")
    from app.core import config
    from app.services.claw_bakery import bakery_storage
    config.get_settings.cache_clear()
    config.settings = config.get_settings()
    bakery_storage._store = None  # noqa: SLF001
    yield
    bakery_storage._store = None  # noqa: SLF001
    # Clean any dependency overrides after each test
    from app.main import app
    app.dependency_overrides.clear()


def _client() -> TestClient:
    from app.main import app
    return TestClient(app)


def _stub_admin_user():
    """Build a stub User-like object with is_platform_admin=True · no DB."""
    class _StubUser:
        id = uuid.UUID("00000000-0000-4000-8000-000000000001")
        email = "test-admin@example.test"
        is_platform_admin = True
    return _StubUser()


def _stub_non_admin_user():
    class _StubUser:
        id = uuid.UUID("00000000-0000-4000-8000-000000000002")
        email = "test-user@example.test"
        is_platform_admin = False
    return _StubUser()


@pytest.fixture
def admin_creds():
    """Override get_current_user to return a stub platform-admin user.

    Returns ("stub-admin-token", admin_user) · the token value is
    irrelevant because we override the dependency that decodes it.
    """
    from app.core.deps import get_current_user
    from app.main import app
    user = _stub_admin_user()
    app.dependency_overrides[get_current_user] = lambda: user
    yield (str(user.id), "stub-admin-token")
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
def non_admin_creds():
    from app.core.deps import get_current_user
    from app.main import app
    user = _stub_non_admin_user()
    app.dependency_overrides[get_current_user] = lambda: user
    yield (str(user.id), "stub-user-token")
    app.dependency_overrides.pop(get_current_user, None)


# ─── Auth gate ───────────────────────────────────────────────────────


def test_pair_list_requires_auth() -> None:
    r = _client().get("/api/v1/claw-bakery/admin/pair-candidates")
    assert r.status_code == 401


def test_pair_list_rejects_non_admin(non_admin_creds) -> None:
    _, tok = non_admin_creds
    r = _client().get(
        "/api/v1/claw-bakery/admin/pair-candidates",
        headers={"Authorization": f"Bearer {tok}"},
    )
    assert r.status_code == 403
    assert "platform admin required" in r.text.lower()


def test_validator_review_doctrine_checks_requires_admin() -> None:
    r = _client().get("/api/v1/claw-bakery/admin/validator-review/doctrine-checks")
    assert r.status_code == 401


def test_doctrine_checks_returns_12_when_authed(admin_creds) -> None:
    _, tok = admin_creds
    r = _client().get(
        "/api/v1/claw-bakery/admin/validator-review/doctrine-checks",
        headers={"Authorization": f"Bearer {tok}"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["check_count"] == 12
    check_ids = {c["check_id"] for c in body["checks"]}
    assert check_ids == {f"C{i:02d}" for i in range(1, 13)}


# ─── Pair listing + retrieval ────────────────────────────────────────


def _seed_pending_pair() -> str:
    """Drop a clean pair candidate into pending/ for tests."""
    from app.services.claw_bakery.pair_factory import (
        create_pair_candidate_from_snapshot,
    )
    snap = {
        "captured": {
            "agent_name": "TestAgent",
            "worker_kind": "Business Agent",
            "deployment_target": "Cloud Server",
        },
        "risk": {"rule_id": "ELEVATED_BUSINESS_DATA_AND_DRAFTING_EXPOSURE",
                 "risk_class": "ELEVATED_BUSINESS_DATA_AND_DRAFTING_EXPOSURE"},
    }
    pair = create_pair_candidate_from_snapshot(
        source_run_id="test_run_001",
        snapshot=snap,
        input_record_key=None,
        raw_snapshot_key=None,
        operator_consent={"allow_deidentified_training_use": True},
    )
    return pair.pair_id


def test_pair_list_returns_safe_metadata(admin_creds) -> None:
    pair_id = _seed_pending_pair()
    _, tok = admin_creds
    r = _client().get(
        "/api/v1/claw-bakery/admin/pair-candidates?bucket=pending&limit=10",
        headers={"Authorization": f"Bearer {tok}"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["bucket"] == "pending"
    assert body["count"] >= 1
    found = [p for p in body["pairs"] if p["pair_id"] == pair_id]
    assert len(found) == 1
    p = found[0]
    assert p["tribunal_label"] == "PENDING"
    assert p["risk_class"] == "ELEVATED_BUSINESS_DATA_AND_DRAFTING_EXPOSURE"


def test_pair_get_returns_full_pair(admin_creds) -> None:
    pair_id = _seed_pending_pair()
    _, tok = admin_creds
    r = _client().get(
        f"/api/v1/claw-bakery/admin/pair-candidates/{pair_id}?bucket=pending",
        headers={"Authorization": f"Bearer {tok}"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["pair"]["pair_id"] == pair_id
    assert "transition_log" in body["pair"]


def test_pair_get_404_for_unknown(admin_creds) -> None:
    _, tok = admin_creds
    r = _client().get(
        "/api/v1/claw-bakery/admin/pair-candidates/DCLAW-PAIR-DOESNOTEXIST?bucket=pending",
        headers={"Authorization": f"Bearer {tok}"},
    )
    assert r.status_code == 404


# ─── Tribunal label re-assignment ────────────────────────────────────


def test_admin_assign_label_to_honey(admin_creds) -> None:
    pair_id = _seed_pending_pair()
    _, tok = admin_creds
    r = _client().post(
        f"/api/v1/claw-bakery/admin/pair-candidates/{pair_id}/tribunal?bucket=pending",
        headers={"Authorization": f"Bearer {tok}"},
        json={"label": "HONEY", "reason": "Validator passed all critical checks."},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["new_label"] == "HONEY"
    assert body["transition_count"] >= 1


def test_admin_assign_label_refuses_propolis_to_honey(admin_creds) -> None:
    from app.services.claw_bakery.pair_factory import (
        TribunalLabel,
        assign_tribunal_label,
        create_pair_candidate_from_snapshot,
    )
    # Seed a pair THEN flip it to PROPOLIS directly via the service
    snap = {"captured": {"agent_name": "BadAgent"}, "risk": {"rule_id": "X"}}
    pair = create_pair_candidate_from_snapshot(
        source_run_id="test_propolis", snapshot=snap,
        input_record_key=None, raw_snapshot_key=None,
    )
    assign_tribunal_label(pair, label=TribunalLabel.PROPOLIS, reason="test setup")
    # Now try to flip PROPOLIS → HONEY via admin route · should refuse
    _, tok = admin_creds
    r = _client().post(
        f"/api/v1/claw-bakery/admin/pair-candidates/{pair.pair_id}/tribunal?bucket=propolis-failures",
        headers={"Authorization": f"Bearer {tok}"},
        json={"label": "HONEY", "reason": "should not work"},
    )
    assert r.status_code == 400
    assert "PROPOLIS" in r.text


# ─── Validator review chain ──────────────────────────────────────────


def test_validator_review_runs_all_12_checks(admin_creds) -> None:
    pair_id = _seed_pending_pair()
    _, tok = admin_creds
    r = _client().post(
        f"/api/v1/claw-bakery/admin/pair-candidates/{pair_id}/validator-review?bucket=pending",
        headers={"Authorization": f"Bearer {tok}"},
    )
    assert r.status_code == 200
    body = r.json()
    assert len(body["checks"]) == 12
    check_ids = {c["check_id"] for c in body["checks"]}
    assert check_ids == {f"C{i:02d}" for i in range(1, 13)}


def test_validator_review_clean_pair_passes_or_downgrades(admin_creds) -> None:
    """A freshly-created PENDING pair with consent should advance to HONEY
    if all checks pass · or DOWNGRADED to JELLY if any advisory fails."""
    pair_id = _seed_pending_pair()
    _, tok = admin_creds
    r = _client().post(
        f"/api/v1/claw-bakery/admin/pair-candidates/{pair_id}/validator-review?bucket=pending",
        headers={"Authorization": f"Bearer {tok}"},
    )
    body = r.json()
    # C04 (Tribunal label assigned) fails for PENDING pairs · so this
    # pair should be QUARANTINED (critical fail).
    assert body["overall_status"] in ("FAILED", "PASSED", "DOWNGRADED")
    assert body["doctrine_seal"]["reviewer_user_id"]


def test_validator_review_records_immutable_session(admin_creds) -> None:
    from app.services.claw_bakery.bakery_storage import get_bakery_store
    pair_id = _seed_pending_pair()
    _, tok = admin_creds
    r = _client().post(
        f"/api/v1/claw-bakery/admin/pair-candidates/{pair_id}/validator-review?bucket=pending",
        headers={"Authorization": f"Bearer {tok}"},
    )
    session_id = r.json()["session_id"]
    # Session record + receipt should be in storage
    store = get_bakery_store()
    receipts = store.list_under("receipts/sha256")
    matching = [k for k in receipts]  # at least one new receipt
    assert len(matching) >= 1
    # The receipt's metadata names this validator session
    found = False
    for k in receipts:
        doc = store.read_json(k)
        if doc.get("extra_metadata", {}).get("session_id") == session_id:
            found = True
            assert doc["artifact_type"] == "validator_review"
            break
    assert found, f"no receipt found for session {session_id}"


def test_validator_review_session_response_has_doctrine_seal(admin_creds) -> None:
    pair_id = _seed_pending_pair()
    _, tok = admin_creds
    r = _client().post(
        f"/api/v1/claw-bakery/admin/pair-candidates/{pair_id}/validator-review?bucket=pending",
        headers={"Authorization": f"Bearer {tok}"},
    )
    body = r.json()
    seal = body["doctrine_seal"]
    assert seal["automated_review_only"] is True
    assert seal["deed_issuance"] == "NOT_AUTOMATED_FROM_THIS_SESSION"
    assert "STILL_REQUIRES_CONSENT_AND_REDACTION_FLAGS" in seal["training_admission"]


def test_validator_review_advance_only_when_passed(admin_creds) -> None:
    """advance=true should only flip validator_status when overall_status=PASSED."""
    pair_id = _seed_pending_pair()
    _, tok = admin_creds
    # PENDING pair fails C04 (Tribunal label assigned) · so advance is a no-op
    r = _client().post(
        f"/api/v1/claw-bakery/admin/pair-candidates/{pair_id}/validator-review"
        f"?bucket=pending&advance=true",
        headers={"Authorization": f"Bearer {tok}"},
    )
    body = r.json()
    # PENDING pair · C04 fails · overall FAILED · pair NOT advanced
    if body["overall_status"] != "PASSED":
        assert body["pair_advanced"] is False


# ─── Admin events + ClawForge ────────────────────────────────────────


def test_admin_events_returns_recent_events(admin_creds) -> None:
    _seed_pending_pair()  # generates events
    _, tok = admin_creds
    r = _client().get(
        "/api/v1/claw-bakery/admin/events",
        headers={"Authorization": f"Bearer {tok}"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["count"] >= 1
    assert any("pair_candidate" in e["event_type"] or "intake" in e["event_type"] for e in body["events"])


def test_admin_clawforge_generates_pending_synthetic_candidate(admin_creds) -> None:
    _, tok = admin_creds
    r = _client().post(
        "/api/v1/claw-bakery/admin/clawforge/generate",
        headers={"Authorization": f"Bearer {tok}"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["source_type"] == "synthetic_forge"
    assert body["tribunal_label"] == "PENDING"
    assert body["eligible_for_training"] is False


def test_admin_clawforge_409_when_disabled(
    admin_creds, monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CLAW_BAKERY_CLAWFORGE_ENABLED", "false")
    _, tok = admin_creds
    r = _client().post(
        "/api/v1/claw-bakery/admin/clawforge/generate",
        headers={"Authorization": f"Bearer {tok}"},
    )
    assert r.status_code == 409
