"""eBay Marketplace Account Deletion notification endpoint.

Production URL:
  GET/POST  /api/v1/marketplace/ebay/notifications/account-deletion

  · GET  · verification challenge handler · returns SHA-256 challengeResponse
  · POST · notification receiver · stores raw + receipt + review record

Plus a readiness probe (admin-aware · returns booleans only):
  GET  /api/v1/marketplace/ebay/notifications/account-deletion/readiness

Doctrine: the token, the digest inputs, and the raw payload bodies are
NEVER logged or exposed in any response. The only response body for the
GET handler is `{"challengeResponse": "<hex>"}` per eBay spec.
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse

from app.services.compliance.ebay_account_deletion import (
    NotificationsDisabled,
    VerificationConfigMissing,
    VerificationTokenInvalid,
    compute_challenge_response,
    readiness_status,
    receive_notification,
)


_log = logging.getLogger("api.marketplace.ebay.notifications.account_deletion")

router = APIRouter(
    prefix="/marketplace/ebay/notifications",
    tags=["compliance-ebay"],
)


@router.get("/account-deletion")
def verification_challenge(
    challenge_code: str | None = Query(default=None, max_length=256),
):
    """eBay verification challenge handler.

    eBay's portal performs TWO actions on Save:
      1. A bare GET to the endpoint URL (no query string) as a reachability
         pre-check. If we 4xx/5xx here, eBay never sends the actual
         challenge and the portal Save fails with no specific error.
      2. A GET with `?challenge_code=<unique value>` · the real verification
         challenge. We respond with:
             {"challengeResponse": "<sha256(challenge_code + token + endpoint_url)>"}

    Therefore:
      · bare GET (no challenge_code) → 200 with a benign identifier body
        that does NOT include the token, endpoint URL, or any sensitive
        config. It only confirms the route exists.
      · GET with challenge_code → normal SHA-256 response per eBay spec.

    HTTP 200 · Content-Type: application/json in both cases.
    """
    # Bare reachability ping · safe affirmative response · no secret bits
    if not challenge_code:
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "service": "ebay-marketplace-account-deletion",
                "status": "endpoint_reachable",
                "expects": "GET with ?challenge_code=<value> for verification challenge",
            },
            media_type="application/json",
        )
    try:
        digest = compute_challenge_response(challenge_code)
    except VerificationConfigMissing:
        # Safe error · do NOT include token/endpoint values
        _log.warning(
            "ebay verification challenge received but configuration is missing"
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "eBay account-deletion verification endpoint is not yet "
                "configured. Set EBAY_ACCOUNT_DELETION_ENDPOINT + "
                "EBAY_ACCOUNT_DELETION_VERIFICATION_TOKEN on the server."
            ),
        )
    except VerificationTokenInvalid as exc:
        _log.warning("ebay verification token failed validation · %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "eBay verification token configured but does not meet the "
                "32-80 char alphanumeric+underscore+hyphen contract."
            ),
        )
    except ValueError as exc:
        # Missing/empty challenge_code · should be unreachable because Query
        # enforces min_length=1, but we keep the safety net.
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    # Log only safe metadata · NEVER log challenge_code, token, or digest
    _log.info(
        "ebay verification challenge served · challenge_len=%d response_len=%d",
        len(challenge_code), len(digest),
    )
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"challengeResponse": digest},
        media_type="application/json",
    )


@router.post("/account-deletion")
async def account_deletion_notification(request: Request):
    """Receive an eBay marketplace account deletion notification.

    Stores the raw body immutably, generates a SHA-256 receipt, writes
    a review-queue record, emits a compliance event. Idempotent on the
    eBay-provided event id.
    """
    raw_body = await request.body()
    if not raw_body:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="empty notification body",
        )

    try:
        envelope = receive_notification(raw_body)
    except NotificationsDisabled:
        # Safe error · explicitly disabled by config
        _log.warning(
            "ebay account-deletion notification received but "
            "EBAY_ACCOUNT_DELETION_NOTIFICATIONS_ENABLED=false · rejecting"
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Marketplace account-deletion notifications are not enabled "
                "on this environment."
            ),
        )
    except ValueError as exc:
        _log.warning("ebay account-deletion notification body invalid · %s", exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="notification body is not valid JSON",
        )
    except Exception as exc:  # noqa: BLE001
        # Surface a generic error to eBay so it retries; log details server-side
        _log.exception("ebay account-deletion store failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="notification storage failed · will be retried",
        ) from exc

    # eBay expects HTTP 2xx on success. We return a minimal acknowledgement
    # that includes the compliance event id (useful for support correlation)
    # but never the payload body or any token.
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "received": True,
            "compliance_event_id": envelope["compliance_event_id"],
            "duplicate_of_prior_delivery": envelope["duplicate_of_prior_delivery"],
        },
    )


@router.get("/account-deletion/readiness")
def readiness():
    """Booleans only · never tokens · safe for an unauthenticated probe
    because the response contains zero secret-derivable bits."""
    return readiness_status()
