"""eBay Marketplace Account Deletion / Closure notification handler.

References:
  · https://developer.ebay.com/marketplace-account-deletion
  · eBay requires every Developer account that holds marketplace user
    data to expose an HTTPS endpoint that:
      1. Responds to a GET challenge with sha256(challenge_code +
         verification_token + endpoint_url) in JSON
      2. Accepts POST notifications about user/account deletion or
         closure events and reliably stores/processes them

Doctrine in this module:
  · The verification token is read from app settings · NEVER logged ·
    NEVER returned in any response other than as input to the SHA-256
    digest
  · The endpoint URL used in the digest MUST be the publicly-deployed
    production URL · we do NOT use request.url at runtime because that
    would let an attacker control the digest input
  · POST notifications land in compliance/ebay/account-deletion/ as
    immutable artifacts with SHA-256 receipts
  · Idempotency is keyed by the eBay-provided event id; duplicate
    deliveries are detected and acknowledged with HTTP 200 (no
    duplicate artifact write)
  · NO destructive deletion is triggered from this module · the
    compliance event lifecycle starts in RECEIVED_PENDING_DATA_REVIEW
    and only an explicit operator/admin action advances it
"""
from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Any

from app.core.config import get_settings
from app.services.compliance.storage import (
    ComplianceStore,
    get_compliance_store,
)


_log = logging.getLogger("compliance.ebay.account_deletion")


# ─── Verification token validation ───────────────────────────────────


class VerificationTokenInvalid(ValueError):
    pass


class VerificationConfigMissing(RuntimeError):
    pass


def _validate_token(token: str) -> None:
    """Enforce eBay's verification-token contract:
      · 32-80 chars
      · alphanumeric + underscore + hyphen ONLY
    """
    if not isinstance(token, str):
        raise VerificationTokenInvalid("verification token must be a string")
    if not (32 <= len(token) <= 80):
        raise VerificationTokenInvalid(
            "verification token length must be 32-80 chars"
        )
    if not all(c.isalnum() or c in ("_", "-") for c in token):
        raise VerificationTokenInvalid(
            "verification token must contain only alphanumeric, underscore, hyphen"
        )


def _ensure_config_present() -> tuple[str, str]:
    """Returns (endpoint_url, verification_token) or raises.

    Reads settings at call time (NOT at module-import time) so a Fly
    secret update / env var change is picked up on the next request
    without a restart, and so tests can override per-test.
    """
    s = get_settings()
    endpoint = s.ebay_account_deletion_endpoint
    token = s.ebay_account_deletion_verification_token
    if not endpoint:
        raise VerificationConfigMissing(
            "EBAY_ACCOUNT_DELETION_ENDPOINT is not configured"
        )
    if not endpoint.startswith("https://"):
        raise VerificationConfigMissing(
            "EBAY_ACCOUNT_DELETION_ENDPOINT must be an HTTPS URL"
        )
    if not token:
        raise VerificationConfigMissing(
            "EBAY_ACCOUNT_DELETION_VERIFICATION_TOKEN is not configured"
        )
    _validate_token(token)
    return endpoint, token


# ─── GET challenge handler ───────────────────────────────────────────


def compute_challenge_response(challenge_code: str) -> str:
    """Compute the SHA-256 hex digest eBay expects.

    Order is FIXED by eBay spec:
        sha256(challenge_code + verification_token + endpoint_url)
    """
    endpoint, token = _ensure_config_present()
    if not challenge_code:
        raise ValueError("challenge_code is required")
    digest_input = (challenge_code + token + endpoint).encode("utf-8")
    return hashlib.sha256(digest_input).hexdigest()


# ─── POST notification receiver ──────────────────────────────────────


# Status lifecycle · per founder spec
STATUS_RECEIVED_PENDING_DATA_REVIEW = "RECEIVED_PENDING_DATA_REVIEW"
STATUS_NO_MATCHING_STORED_USER_DATA = "NO_MATCHING_STORED_USER_DATA"
STATUS_MATCHING_DATA_QUARANTINED = "MATCHING_DATA_QUARANTINED"
STATUS_DELETION_OR_ANONYMIZATION_COMPLETED = "DELETION_OR_ANONYMIZATION_COMPLETED"
STATUS_MANUAL_REVIEW_REQUIRED = "MANUAL_REVIEW_REQUIRED"
STATUS_PROCESSING_FAILED = "PROCESSING_FAILED"


class NotificationsDisabled(RuntimeError):
    pass


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _extract_event_id(payload: dict[str, Any]) -> str:
    """Extract a stable event id from eBay's notification envelope.

    eBay's documented schema places the unique id under
    `notification.notificationId` (with `metadata.topic` also present).
    We accept several shapes defensively so a small schema drift on
    eBay's side doesn't break idempotency:

      · notification.notificationId
      · notificationId (top-level)
      · notification.notificationId  (camelCase variant)
      · derived sha256 of canonical payload if none found
    """
    n = payload.get("notification") or {}
    for candidate in (
        n.get("notificationId"),
        n.get("notification_id"),
        payload.get("notificationId"),
        payload.get("notification_id"),
        payload.get("id"),
    ):
        if isinstance(candidate, str) and candidate:
            return candidate
    # Last resort · derive a deterministic id so duplicate raw payloads
    # still dedupe even when eBay omitted the id.
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "derived_sha256_" + hashlib.sha256(canonical).hexdigest()[:32]


def receive_notification(
    raw_body: bytes,
    *,
    store: ComplianceStore | None = None,
) -> dict[str, Any]:
    """Persist a single eBay account-deletion notification.

    Returns the envelope describing what was written. The endpoint
    handler turns this into a 200 response if the envelope was created
    (whether the artifact was a new write or a known idempotent duplicate).

    Raises:
      · NotificationsDisabled · when the kill-switch env var is False
      · ValueError · when the payload is not valid JSON
      · ComplianceKeyExistsError (from storage) for non-idempotency races
        (would only happen if two distinct payloads coerced to the same
        event_id · we keep the first write and report this as a conflict
        to the caller, who returns 409)
    """
    if not get_settings().ebay_account_deletion_notifications_enabled:
        raise NotificationsDisabled(
            "EBAY_ACCOUNT_DELETION_NOTIFICATIONS_ENABLED is false"
        )

    store = store or get_compliance_store()

    try:
        payload = json.loads(raw_body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"notification body is not valid UTF-8 JSON: {exc}") from exc

    if not isinstance(payload, dict):
        raise ValueError("notification body must be a JSON object")

    event_id = _extract_event_id(payload)
    compliance_event_id = f"EBAY-ACCTDEL-{event_id}"
    received_at = _now_iso()

    # Idempotency claim · if this event was already processed, return the
    # existing envelope marker.
    was_fresh, idem_key = store.claim_idempotency(
        dedupe_id=compliance_event_id,
        payload={
            "compliance_event_id": compliance_event_id,
            "first_received_at": received_at,
        },
    )

    if not was_fresh:
        return {
            "compliance_event_id": compliance_event_id,
            "received_at": received_at,
            "duplicate_of_prior_delivery": True,
            "idempotency_key": idem_key,
            "publicly_visible": False,
        }

    # First delivery · write immutable raw notification + receipt + review record
    raw_artifact = store.put_raw_notification(compliance_event_id, raw_body)

    receipt = {
        "receipt_id": f"EBAY-RECEIPT-{event_id}",
        "compliance_event_id": compliance_event_id,
        "artifact_key": raw_artifact.key,
        "byte_size": raw_artifact.byte_size,
        "sha256": raw_artifact.sha256,
        "created_at": received_at,
    }
    receipt_artifact = store.put_receipt(receipt["receipt_id"], receipt)

    review = {
        "compliance_event_id": compliance_event_id,
        "source": "EBAY",
        "topic": (payload.get("metadata") or {}).get("topic")
            or "MARKETPLACE_ACCOUNT_DELETION",
        "received_at": received_at,
        "payload_artifact_path": raw_artifact.key,
        "sha256_receipt_path": receipt_artifact.key,
        "processing_status": STATUS_RECEIVED_PENDING_DATA_REVIEW,
        "data_review_required": True,
        "deletion_or_anonymization_status": "PENDING",
        "publicly_visible": False,
        "doctrine_note": (
            "Public eBay listing observations and account-linked retained "
            "records are not the same data class. Deletion or anonymization "
            "must target only records linked to the deleted marketplace "
            "account. Review by an authorized operator before any erasure."
        ),
    }
    store.put_review_record(compliance_event_id, review)

    store.append_event(
        f"event_{event_id}",
        {
            "event_id": f"event_{event_id}",
            "compliance_event_id": compliance_event_id,
            "kind": "ebay.account_deletion.received",
            "at": received_at,
            "artifact_sha256": raw_artifact.sha256,
        },
    )

    # Audit-log entry · only safe metadata · never the payload body.
    _log.info(
        "ebay account-deletion notification stored · compliance_event_id=%s "
        "byte_size=%d sha256=%s",
        compliance_event_id,
        raw_artifact.byte_size,
        raw_artifact.sha256,
    )

    return {
        "compliance_event_id": compliance_event_id,
        "received_at": received_at,
        "artifact_key": raw_artifact.key,
        "artifact_sha256": raw_artifact.sha256,
        "receipt_id": receipt["receipt_id"],
        "processing_status": STATUS_RECEIVED_PENDING_DATA_REVIEW,
        "duplicate_of_prior_delivery": False,
        "publicly_visible": False,
    }


# ─── Readiness ───────────────────────────────────────────────────────


def readiness_status() -> dict[str, Any]:
    """Return SAFE booleans · never tokens, never partial token values."""
    s = get_settings()
    endpoint_ok = bool(s.ebay_account_deletion_endpoint) and \
        s.ebay_account_deletion_endpoint.startswith("https://")
    token_present = bool(s.ebay_account_deletion_verification_token)
    token_valid = False
    if token_present:
        try:
            _validate_token(s.ebay_account_deletion_verification_token)
            token_valid = True
        except VerificationTokenInvalid:
            token_valid = False
    return {
        "integration": "ebay_marketplace_account_deletion",
        "endpoint_configured": endpoint_ok,
        "verification_token_configured": token_present,
        "verification_token_format_valid": token_valid,
        "notifications_enabled": s.ebay_account_deletion_notifications_enabled,
        "ready_for_ebay_verification": endpoint_ok and token_valid,
    }
