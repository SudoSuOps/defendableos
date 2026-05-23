"""eBay OAuth · client_credentials flow + in-memory token cache.

Endpoint matrix:
  · sandbox    · https://api.sandbox.ebay.com/identity/v1/oauth2/token
  · production · https://api.ebay.com/identity/v1/oauth2/token

Doctrine:
  · Cert ID is the Client Secret · NEVER logged · only used in the Basic
    auth header we send to eBay
  · Access tokens NEVER logged in full · only first 8 chars + expiry for
    debugging
  · Cache in-memory per-process · refresh 100s before expiry · auto-retry
    once on 401 in case of clock skew
  · No global mutable state at import time · cache lives behind a getter

Reference: https://developer.ebay.com/api-docs/static/oauth-client-credentials-grant.html
"""
from __future__ import annotations

import base64
import logging
import threading
import time
from dataclasses import dataclass
from typing import Any

import httpx

from app.core.config import get_settings


_log = logging.getLogger("integrations.ebay.oauth")


SANDBOX_TOKEN_URL = "https://api.sandbox.ebay.com/identity/v1/oauth2/token"
PRODUCTION_TOKEN_URL = "https://api.ebay.com/identity/v1/oauth2/token"

# Default scope for public-data access (Browse API + most read APIs)
DEFAULT_SCOPE = "https://api.ebay.com/oauth/api_scope"

# Refresh the token this many seconds BEFORE eBay-reported expiry
_REFRESH_SAFETY_MARGIN_SECONDS = 100


class EbayOAuthConfigMissing(RuntimeError):
    """Raised when EBAY_APP_ID or EBAY_CERT_ID are not configured."""


class EbayOAuthError(RuntimeError):
    """Raised when eBay's token endpoint returns a non-2xx."""


@dataclass
class CachedToken:
    access_token: str
    token_type: str        # always 'Bearer' for client_credentials
    expires_at_epoch: int  # absolute UTC epoch seconds
    scope: str
    environment: str       # 'sandbox' | 'production'

    def is_fresh(self) -> bool:
        return time.time() + _REFRESH_SAFETY_MARGIN_SECONDS < self.expires_at_epoch

    def safe_metadata(self) -> dict[str, Any]:
        """Return non-secret metadata · suitable for /admin readiness probes."""
        return {
            "token_present": True,
            "token_type": self.token_type,
            "token_prefix": self.access_token[:8] + "...",  # debugging only
            "expires_in_seconds": max(0, int(self.expires_at_epoch - time.time())),
            "scope": self.scope,
            "environment": self.environment,
        }


# Process-local cache · protected by a lock for parallel-request safety
_cache: CachedToken | None = None
_cache_lock = threading.Lock()


def reset_cache_for_tests() -> None:
    """Clear the token cache · tests only."""
    global _cache
    with _cache_lock:
        _cache = None


def _token_url() -> str:
    env = get_settings().ebay_environment.lower()
    if env == "production":
        return PRODUCTION_TOKEN_URL
    return SANDBOX_TOKEN_URL


def _basic_auth_header() -> str:
    """Construct the Basic auth header eBay expects.

    Returns the header VALUE (caller adds 'Authorization' key). Cert ID
    is held only in this stack frame · not stored anywhere else.
    """
    s = get_settings()
    if not s.ebay_app_id or not s.ebay_cert_id:
        raise EbayOAuthConfigMissing(
            "EBAY_APP_ID and EBAY_CERT_ID must both be configured"
        )
    raw = f"{s.ebay_app_id}:{s.ebay_cert_id}".encode("utf-8")
    encoded = base64.b64encode(raw).decode("ascii")
    return f"Basic {encoded}"


def _fetch_new_token(scope: str = DEFAULT_SCOPE, timeout: float = 30.0) -> CachedToken:
    """Hit eBay's token endpoint · POST form-urlencoded · return CachedToken.

    Does NOT touch the cache · the caller decides whether to install.
    """
    url = _token_url()
    headers = {
        "Authorization": _basic_auth_header(),
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
    }
    body = {"grant_type": "client_credentials", "scope": scope}

    started_at = time.time()
    with httpx.Client(timeout=timeout) as client:
        resp = client.post(url, headers=headers, data=body)

    if resp.status_code >= 400:
        # Safe error · NEVER include Authorization header or response body
        # verbatim because eBay sometimes echoes the credentials on certain
        # error codes. Log only status + status message.
        _log.error(
            "ebay oauth token fetch failed · status=%d reason=%s url=%s",
            resp.status_code, resp.reason_phrase, url,
        )
        raise EbayOAuthError(
            f"eBay OAuth token endpoint returned HTTP {resp.status_code}"
        )

    data = resp.json()
    access_token = data.get("access_token")
    expires_in = int(data.get("expires_in") or 0)
    token_type = data.get("token_type", "Bearer")
    if not access_token or expires_in <= 0:
        raise EbayOAuthError(
            "eBay OAuth response missing access_token or expires_in"
        )

    env = get_settings().ebay_environment.lower()
    cached = CachedToken(
        access_token=access_token,
        token_type=token_type,
        expires_at_epoch=int(started_at) + expires_in,
        scope=scope,
        environment="production" if env == "production" else "sandbox",
    )
    _log.info(
        "ebay oauth token fetched · env=%s token_prefix=%s... expires_in=%ds scope=%s",
        cached.environment, cached.access_token[:8], expires_in, scope,
    )
    return cached


def get_application_token(scope: str = DEFAULT_SCOPE) -> CachedToken:
    """Return a fresh CachedToken · using cache when fresh."""
    global _cache
    with _cache_lock:
        if _cache is not None and _cache.scope == scope and _cache.is_fresh():
            return _cache
        _cache = _fetch_new_token(scope=scope)
        return _cache


def invalidate_cache() -> None:
    """Drop the cached token (e.g. after a 401 response from a downstream API)."""
    global _cache
    with _cache_lock:
        _cache = None


def readiness_status() -> dict[str, Any]:
    """SAFE readiness for /admin probes · no secret bits."""
    s = get_settings()
    app_id_present = bool(s.ebay_app_id)
    cert_id_present = bool(s.ebay_cert_id)
    dev_id_present = bool(s.ebay_dev_id)
    env = (s.ebay_environment or "sandbox").lower()
    # Token cache state (safe metadata · no token value)
    cache_state: dict[str, Any] = {"cached_token_present": False}
    with _cache_lock:
        if _cache is not None:
            cache_state = {
                "cached_token_present": True,
                "cached_token_fresh": _cache.is_fresh(),
                "cached_token_expires_in_seconds": max(
                    0, int(_cache.expires_at_epoch - time.time())
                ),
                "cached_token_scope": _cache.scope,
            }
    return {
        "integration": "ebay_oauth_client_credentials",
        "environment": env,
        "app_id_configured": app_id_present,
        "cert_id_configured": cert_id_present,
        "dev_id_configured": dev_id_present,
        "ready_for_token_fetch": app_id_present and cert_id_present,
        **cache_state,
    }
