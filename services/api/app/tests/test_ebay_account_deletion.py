"""eBay Marketplace Account Deletion endpoint tests.

Covers:
  · GET verification challenge · digest order + content type + safe errors
  · POST notification receiver · immutable raw write + receipt + review
  · Idempotency · duplicate event_id is acknowledged without rewriting
  · Secret hygiene · token never appears in logs or response bodies
  · Readiness probe · booleans only · no token leakage
"""
from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


# Known fixture · token + endpoint + challenge are public test values · the
# expected digest is precomputed by the same SHA-256 implementation eBay
# uses (Python's hashlib · documented in the eBay portal).
FIXTURE_ENDPOINT = "https://api.defendableos.com/api/v1/marketplace/ebay/notifications/account-deletion"
FIXTURE_TOKEN = "test_token_abcdef0123456789abcdef0123456789abcd"
FIXTURE_CHALLENGE = "challenge_value_42"
FIXTURE_EXPECTED_DIGEST = hashlib.sha256(
    (FIXTURE_CHALLENGE + FIXTURE_TOKEN + FIXTURE_ENDPOINT).encode("utf-8")
).hexdigest()


@pytest.fixture(autouse=True)
def _isolated_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Each test gets fresh env + fresh compliance store + fresh settings."""
    monkeypatch.setenv("COMPLIANCE_STORAGE_DRIVER", "local")
    monkeypatch.setenv("COMPLIANCE_LOCAL_ROOT", str(tmp_path / "compliance"))
    monkeypatch.setenv("EBAY_ACCOUNT_DELETION_ENDPOINT", FIXTURE_ENDPOINT)
    monkeypatch.setenv("EBAY_ACCOUNT_DELETION_VERIFICATION_TOKEN", FIXTURE_TOKEN)
    monkeypatch.setenv("EBAY_ACCOUNT_DELETION_NOTIFICATIONS_ENABLED", "true")

    # Reset cached singletons
    from app.core import config
    from app.services.compliance import storage
    config.get_settings.cache_clear()
    config.settings = config.get_settings()
    storage.reset_compliance_store_for_tests()
    yield
    config.get_settings.cache_clear()
    config.settings = config.get_settings()
    storage.reset_compliance_store_for_tests()


def _client() -> TestClient:
    from app.main import app
    return TestClient(app)


# ─── GET verification challenge ──────────────────────────────────────


def test_get_verification_challenge_returns_correct_digest() -> None:
    resp = _client().get(
        "/api/v1/marketplace/ebay/notifications/account-deletion",
        params={"challenge_code": FIXTURE_CHALLENGE},
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("application/json")
    assert resp.json() == {"challengeResponse": FIXTURE_EXPECTED_DIGEST}


def test_get_digest_order_is_challenge_token_endpoint() -> None:
    """Doctrine: order MUST be challenge_code + verification_token + endpoint_url.
    Any other order would silently fail eBay's verification."""
    resp = _client().get(
        "/api/v1/marketplace/ebay/notifications/account-deletion",
        params={"challenge_code": FIXTURE_CHALLENGE},
    )
    body = resp.json()
    # Re-derive locally with the exact spec'd order
    expected = hashlib.sha256(
        (FIXTURE_CHALLENGE + FIXTURE_TOKEN + FIXTURE_ENDPOINT).encode("utf-8")
    ).hexdigest()
    assert body["challengeResponse"] == expected
    # Sanity: a swapped order must NOT match
    wrong_order = hashlib.sha256(
        (FIXTURE_TOKEN + FIXTURE_CHALLENGE + FIXTURE_ENDPOINT).encode("utf-8")
    ).hexdigest()
    assert body["challengeResponse"] != wrong_order


def test_get_bare_reachability_ping_returns_200_safe() -> None:
    """eBay's portal pings the endpoint with NO query string first as a
    reachability check before sending the actual challenge. We MUST
    respond 200 with a non-secret body or eBay rejects the URL and never
    sends the real challenge."""
    resp = _client().get(
        "/api/v1/marketplace/ebay/notifications/account-deletion",
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("application/json")
    body = resp.json()
    assert body["service"] == "ebay-marketplace-account-deletion"
    assert body["status"] == "endpoint_reachable"
    # Bare ping must NOT leak the token OR the endpoint URL
    blob = resp.text.lower()
    assert FIXTURE_TOKEN.lower() not in blob
    assert "api.defendableos.com" not in blob


def test_get_empty_challenge_code_returns_200_safe() -> None:
    """`?challenge_code=` (empty value) behaves the same as bare GET."""
    resp = _client().get(
        "/api/v1/marketplace/ebay/notifications/account-deletion?challenge_code=",
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "endpoint_reachable"


def test_get_missing_token_returns_503_without_leaking_endpoint_or_token(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("EBAY_ACCOUNT_DELETION_VERIFICATION_TOKEN", "")
    from app.core import config
    config.get_settings.cache_clear()
    config.settings = config.get_settings()
    resp = _client().get(
        "/api/v1/marketplace/ebay/notifications/account-deletion",
        params={"challenge_code": FIXTURE_CHALLENGE},
    )
    assert resp.status_code == 503
    blob = resp.text.lower()
    assert FIXTURE_TOKEN.lower() not in blob


def test_get_invalid_token_format_returns_503_safely(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Too short · violates 32-80 contract
    monkeypatch.setenv("EBAY_ACCOUNT_DELETION_VERIFICATION_TOKEN", "tooshort")
    from app.core import config
    config.get_settings.cache_clear()
    config.settings = config.get_settings()
    resp = _client().get(
        "/api/v1/marketplace/ebay/notifications/account-deletion",
        params={"challenge_code": FIXTURE_CHALLENGE},
    )
    assert resp.status_code == 503
    assert "tooshort" not in resp.text.lower()


def test_get_response_is_json_content_type() -> None:
    resp = _client().get(
        "/api/v1/marketplace/ebay/notifications/account-deletion",
        params={"challenge_code": FIXTURE_CHALLENGE},
    )
    assert resp.headers["content-type"].startswith("application/json")


def test_get_does_not_log_token(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """The verification token must NEVER appear in logs.

    Note: the challenge_code is intentionally in the URL query string per
    eBay spec, so HTTP-access loggers (uvicorn / httpx test client) may
    log it. Challenge codes are short-lived and not secrets · only the
    token is. We assert ONLY the token + computed digest do not appear
    in any log message from this app's own loggers.
    """
    caplog.set_level(logging.DEBUG)
    resp = _client().get(
        "/api/v1/marketplace/ebay/notifications/account-deletion",
        params={"challenge_code": FIXTURE_CHALLENGE},
    )
    digest = resp.json()["challengeResponse"]
    # Only inspect our application's logger output · NOT httpx/uvicorn access
    app_log_blob = "\n".join(
        r.getMessage() for r in caplog.records
        if r.name.startswith("api.marketplace.ebay")
           or r.name.startswith("compliance.")
    )
    assert FIXTURE_TOKEN not in app_log_blob
    assert digest not in app_log_blob
    # And cross-cutting · no app logger leaks the token regardless of name
    full_log_blob = "\n".join(r.getMessage() for r in caplog.records)
    assert FIXTURE_TOKEN not in full_log_blob


# ─── POST notification receiver ──────────────────────────────────────


SAMPLE_NOTIFICATION = {
    "metadata": {
        "topic": "MARKETPLACE_ACCOUNT_DELETION",
        "schemaVersion": "1.0",
        "deprecated": False,
    },
    "notification": {
        "notificationId": "test-notification-id-001",
        "eventDate": "2026-05-23T18:00:00.000Z",
        "publishDate": "2026-05-23T18:00:01.000Z",
        "publishAttemptCount": 1,
        "data": {
            "username": "ebay_user_x",
            "userId": "ma8vp1jySJC",
            "eiasToken": "nY+sHZ2PrBmdj6wVnY+sEZ2PrA2dj6...",
        },
    },
}


def test_post_accepts_notification_and_returns_200() -> None:
    resp = _client().post(
        "/api/v1/marketplace/ebay/notifications/account-deletion",
        json=SAMPLE_NOTIFICATION,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["received"] is True
    assert body["compliance_event_id"].startswith("EBAY-ACCTDEL-")
    assert body["duplicate_of_prior_delivery"] is False


def test_post_stores_immutable_raw_artifact() -> None:
    _client().post(
        "/api/v1/marketplace/ebay/notifications/account-deletion",
        json=SAMPLE_NOTIFICATION,
    )
    from app.services.compliance.storage import get_compliance_store
    store = get_compliance_store()
    raw_keys = store.list_under("ebay/account-deletion/raw-notifications")
    assert len(raw_keys) == 1
    raw = store.driver.read(raw_keys[0])
    parsed = json.loads(raw.decode("utf-8"))
    assert parsed["notification"]["notificationId"] == "test-notification-id-001"


def test_post_generates_sha256_receipt() -> None:
    _client().post(
        "/api/v1/marketplace/ebay/notifications/account-deletion",
        json=SAMPLE_NOTIFICATION,
    )
    from app.services.compliance.storage import get_compliance_store
    store = get_compliance_store()
    raw_keys = store.list_under("ebay/account-deletion/raw-notifications")
    receipt_keys = store.list_under("ebay/account-deletion/receipts")
    assert len(receipt_keys) == 1
    raw_bytes = store.driver.read(raw_keys[0])
    expected_sha = hashlib.sha256(raw_bytes).hexdigest()
    receipt = store.read_json(receipt_keys[0])
    assert receipt["sha256"] == expected_sha
    # Receipt should reference the raw artifact key
    assert receipt["artifact_key"] == raw_keys[0]


def test_post_review_record_status_lifecycle_initial() -> None:
    _client().post(
        "/api/v1/marketplace/ebay/notifications/account-deletion",
        json=SAMPLE_NOTIFICATION,
    )
    from app.services.compliance.storage import get_compliance_store
    store = get_compliance_store()
    review_keys = store.list_under("ebay/account-deletion/review-queue")
    assert len(review_keys) == 1
    review = store.read_json(review_keys[0])
    assert review["processing_status"] == "RECEIVED_PENDING_DATA_REVIEW"
    assert review["data_review_required"] is True
    assert review["deletion_or_anonymization_status"] == "PENDING"
    assert review["publicly_visible"] is False
    assert review["source"] == "EBAY"
    assert review["topic"] == "MARKETPLACE_ACCOUNT_DELETION"


def test_post_duplicate_event_is_idempotent() -> None:
    c = _client()
    first = c.post(
        "/api/v1/marketplace/ebay/notifications/account-deletion",
        json=SAMPLE_NOTIFICATION,
    )
    second = c.post(
        "/api/v1/marketplace/ebay/notifications/account-deletion",
        json=SAMPLE_NOTIFICATION,
    )
    assert first.status_code == 200 and second.status_code == 200
    assert first.json()["duplicate_of_prior_delivery"] is False
    assert second.json()["duplicate_of_prior_delivery"] is True
    # Same compliance_event_id across both deliveries
    assert first.json()["compliance_event_id"] == second.json()["compliance_event_id"]
    # Only ONE raw artifact written
    from app.services.compliance.storage import get_compliance_store
    store = get_compliance_store()
    raw_keys = store.list_under("ebay/account-deletion/raw-notifications")
    assert len(raw_keys) == 1


def test_post_rejected_when_notifications_disabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("EBAY_ACCOUNT_DELETION_NOTIFICATIONS_ENABLED", "false")
    from app.core import config
    config.get_settings.cache_clear()
    config.settings = config.get_settings()
    resp = _client().post(
        "/api/v1/marketplace/ebay/notifications/account-deletion",
        json=SAMPLE_NOTIFICATION,
    )
    assert resp.status_code == 503


def test_post_rejected_on_invalid_json() -> None:
    resp = _client().post(
        "/api/v1/marketplace/ebay/notifications/account-deletion",
        data="{ this is not json",
        headers={"Content-Type": "application/json"},
    )
    assert resp.status_code == 400


def test_post_rejected_on_empty_body() -> None:
    resp = _client().post(
        "/api/v1/marketplace/ebay/notifications/account-deletion",
        data=b"",
        headers={"Content-Type": "application/json"},
    )
    assert resp.status_code == 400


def test_post_does_not_expose_payload_in_response() -> None:
    resp = _client().post(
        "/api/v1/marketplace/ebay/notifications/account-deletion",
        json=SAMPLE_NOTIFICATION,
    )
    blob = resp.text
    # User-identifying fields from the payload must NOT appear in the response
    assert "ebay_user_x" not in blob
    assert "ma8vp1jySJC" not in blob
    assert "eiasToken" not in blob


def test_post_does_not_log_token_or_raw_body(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.DEBUG)
    _client().post(
        "/api/v1/marketplace/ebay/notifications/account-deletion",
        json=SAMPLE_NOTIFICATION,
    )
    log_blob = "\n".join(r.getMessage() for r in caplog.records)
    assert FIXTURE_TOKEN not in log_blob
    assert "ebay_user_x" not in log_blob
    assert "eiasToken" not in log_blob


# ─── Readiness probe ─────────────────────────────────────────────────


def test_readiness_returns_safe_booleans() -> None:
    resp = _client().get(
        "/api/v1/marketplace/ebay/notifications/account-deletion/readiness",
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["integration"] == "ebay_marketplace_account_deletion"
    assert body["endpoint_configured"] is True
    assert body["verification_token_configured"] is True
    assert body["verification_token_format_valid"] is True
    assert body["notifications_enabled"] is True
    assert body["ready_for_ebay_verification"] is True
    # NO TOKEN VALUE anywhere
    blob = resp.text
    assert FIXTURE_TOKEN not in blob


def test_readiness_with_no_config_returns_not_ready(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("EBAY_ACCOUNT_DELETION_VERIFICATION_TOKEN", "")
    monkeypatch.setenv("EBAY_ACCOUNT_DELETION_NOTIFICATIONS_ENABLED", "false")
    from app.core import config
    config.get_settings.cache_clear()
    config.settings = config.get_settings()
    resp = _client().get(
        "/api/v1/marketplace/ebay/notifications/account-deletion/readiness",
    )
    body = resp.json()
    assert body["verification_token_configured"] is False
    assert body["ready_for_ebay_verification"] is False
