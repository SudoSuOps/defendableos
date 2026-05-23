"""Deterministic redaction · PII / credential / address scrubbing.

The Claw Bakery's training pipeline NEVER admits a record until
redaction_status == COMPLETED. This module performs the actual scrub.

Scope:
  · email addresses
  · physical addresses (street numbers / common street suffixes)
  · phone numbers
  · credit card numbers (Luhn-shaped sequences)
  · access tokens / API keys (common formats)
  · SSH key fragments
  · .env-style KEY=VALUE pairs
  · obvious customer names tagged by the operator

This is not a complete PII engine · it is a defendable conservative
first pass. Any candidate that still contains a hit after scrubbing
is REFUSED (raises RedactionRefusal). The redaction status is set
by the caller after the scrub returns clean.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field


_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_PHONE_RE = re.compile(r"(?<!\d)(?:\+?\d{1,3}[\s\-.]?)?(?:\(?\d{2,4}\)?[\s\-.]?){2,4}\d{2,4}(?!\d)")
_STREET_RE = re.compile(
    r"\b\d{1,6}\s+[A-Z][A-Za-z]+\s+(Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Court|Ct|Way|Place|Pl)\b",
    re.IGNORECASE,
)
_CC_RE = re.compile(r"\b(?:\d[ -]*?){13,19}\b")
_TOKEN_RE = re.compile(
    r"\b(sk-[A-Za-z0-9_\-]{20,}|ghp_[A-Za-z0-9]{20,}|"
    r"AKIA[0-9A-Z]{16}|"
    r"Bearer\s+[A-Za-z0-9._\-]{20,}|"
    r"xox[abpr]-[A-Za-z0-9\-]+)\b"
)
_SSH_KEY_RE = re.compile(r"-----BEGIN [A-Z ]+PRIVATE KEY-----.*?-----END [A-Z ]+PRIVATE KEY-----", re.DOTALL)
_ENV_KV_RE = re.compile(r"\b([A-Z][A-Z0-9_]{2,})\s*=\s*([^\s'\"]+)\b")


class RedactionRefusal(ValueError):
    """Raised when a record still contains PII after the scrub completes."""


@dataclass
class RedactionResult:
    redacted_text: str
    hits: dict[str, int] = field(default_factory=dict)
    clean_after_scrub: bool = True


def redact_text(text: str, *, operator_named_pii: list[str] | None = None) -> RedactionResult:
    """Return a redacted copy of `text` and a per-class hit count."""
    if not text:
        return RedactionResult(redacted_text="", hits={}, clean_after_scrub=True)
    hits: dict[str, int] = {}
    out = text

    def _scrub(pattern: re.Pattern[str], placeholder: str, klass: str) -> None:
        nonlocal out
        matches = pattern.findall(out)
        if matches:
            hits[klass] = hits.get(klass, 0) + len(matches)
            out = pattern.sub(placeholder, out)

    # Order matters · the phone regex is greedy enough to swallow a PAN,
    # so PANs and tokens MUST be scrubbed first. SSH private keys are
    # spans of multi-line text, scrub them before anything else.
    _scrub(_SSH_KEY_RE, "[REDACTED_SSH_PRIVATE_KEY]", "ssh_key")
    _scrub(_TOKEN_RE, "[REDACTED_TOKEN]", "access_token")
    _scrub(_CC_RE, "[REDACTED_PAN]", "credit_card")
    _scrub(_EMAIL_RE, "[REDACTED_EMAIL]", "email")
    _scrub(_PHONE_RE, "[REDACTED_PHONE]", "phone")
    _scrub(_STREET_RE, "[REDACTED_ADDRESS]", "street_address")

    # .env style scrubbing replaces the VALUE only, keeping the KEY for
    # context (KEY=[REDACTED]).
    def _env_sub(match: re.Match[str]) -> str:
        return f"{match.group(1)}=[REDACTED]"

    new_out, n = _ENV_KV_RE.subn(_env_sub, out)
    if n:
        hits["env_kv"] = hits.get("env_kv", 0) + n
        out = new_out

    # Operator-named PII (verbatim string replacement)
    for name in operator_named_pii or []:
        if name and name in out:
            count = out.count(name)
            hits["operator_named"] = hits.get("operator_named", 0) + count
            out = out.replace(name, "[REDACTED_NAME]")

    # Final residual check · if a PII regex still hits, refuse.
    residual = (
        _EMAIL_RE.search(out)
        or _PHONE_RE.search(out)
        or _STREET_RE.search(out)
        or _CC_RE.search(out)
        or _TOKEN_RE.search(out)
        or _SSH_KEY_RE.search(out)
    )
    clean = residual is None
    return RedactionResult(redacted_text=out, hits=hits, clean_after_scrub=clean)


def assert_redacted(result: RedactionResult) -> None:
    if not result.clean_after_scrub:
        raise RedactionRefusal("residual PII detected after scrub · refuse training admission")
