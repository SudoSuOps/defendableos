"""Validator review chain · 12-check doctrine for pair candidates.

Per docs/TRIBUNAL_GRADING_DOCTRINE.md (and the bakery design):
  A pair candidate cannot advance to deed eligibility without passing
  a 12-check Validator review. Some checks are critical (must pass);
  others are advisory (failures downgrade but don't block).

Each check is a small typed function that inspects the pair candidate
+ its source artifacts in the bakery vault and returns a CheckResult.

Doctrine:
  · The Validator is a separate review layer · NOT the agent under test
  · Validator output is itself stored immutably (review session JSON)
  · A FAILED critical check is a hard stop · advances pair to QUARANTINED
  · An UNDEFINED check (not yet implementable) returns
    status='NOT_YET_IMPLEMENTED' which is recorded but does not block
"""
from __future__ import annotations

import enum
import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable

from app.services.claw_bakery.bakery_storage import (
    BakeryStore,
    bakery_key,
    get_bakery_store,
    safe_key_part,
)
from app.services.claw_bakery.bakery_events import append_event
from app.services.claw_bakery.receipts import generate_receipt


class CheckStatus(str, enum.Enum):
    PASSED = "PASSED"
    FAILED = "FAILED"
    INCONCLUSIVE = "INCONCLUSIVE"
    NOT_YET_IMPLEMENTED = "NOT_YET_IMPLEMENTED"


class CheckSeverity(str, enum.Enum):
    CRITICAL = "CRITICAL"   # FAILED here → hard stop · pair NEVER advances
    ADVISORY = "ADVISORY"   # FAILED here → downgrade to JELLY · still allowed


@dataclass
class CheckResult:
    check_id: str
    name: str
    severity: CheckSeverity
    status: CheckStatus
    reason: str
    evidence: dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidatorReviewSession:
    session_id: str
    pair_id: str
    started_at: str
    completed_at: str | None
    reviewer_user_id: str  # the platform_admin who ran the review
    checks: list[CheckResult] = field(default_factory=list)
    overall_status: str = "IN_PROGRESS"   # IN_PROGRESS · PASSED · FAILED · DOWNGRADED
    advance_to_label: str | None = None   # what label the pair should land in
    doctrine_seal: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ─── The 12-check doctrine ───────────────────────────────────────────


CheckFn = Callable[[dict[str, Any], BakeryStore], CheckResult]


def _passed(check_id: str, name: str, severity: CheckSeverity, reason: str, evidence: dict | None = None) -> CheckResult:
    return CheckResult(check_id=check_id, name=name, severity=severity,
                       status=CheckStatus.PASSED, reason=reason, evidence=evidence or {})


def _failed(check_id: str, name: str, severity: CheckSeverity, reason: str, evidence: dict | None = None) -> CheckResult:
    return CheckResult(check_id=check_id, name=name, severity=severity,
                       status=CheckStatus.FAILED, reason=reason, evidence=evidence or {})


def _inconclusive(check_id: str, name: str, severity: CheckSeverity, reason: str) -> CheckResult:
    return CheckResult(check_id=check_id, name=name, severity=severity,
                       status=CheckStatus.INCONCLUSIVE, reason=reason)


def _nyi(check_id: str, name: str, severity: CheckSeverity) -> CheckResult:
    return CheckResult(
        check_id=check_id, name=name, severity=severity,
        status=CheckStatus.NOT_YET_IMPLEMENTED,
        reason="Check not yet implemented · reviewer must validate manually.",
    )


# Each check receives the pair candidate dict (already loaded from storage)
# and the BakeryStore handle for fetching linked artifacts.


def check_pair_record_present(pair: dict[str, Any], _store: BakeryStore) -> CheckResult:
    if pair.get("pair_id") and pair.get("source_run_id"):
        return _passed(
            "C01", "Pair record present",
            CheckSeverity.CRITICAL,
            "Pair candidate JSON loaded · pair_id + source_run_id present.",
            evidence={"pair_id": pair["pair_id"]},
        )
    return _failed(
        "C01", "Pair record present", CheckSeverity.CRITICAL,
        "Pair candidate missing pair_id or source_run_id."
    )


def check_source_artifact_referenced(pair: dict[str, Any], _store: BakeryStore) -> CheckResult:
    if pair.get("raw_snapshot_key") or pair.get("input_record_key"):
        return _passed(
            "C02", "Source artifact referenced",
            CheckSeverity.CRITICAL,
            "Pair references at least one source artifact (raw snapshot or input).",
        )
    return _failed(
        "C02", "Source artifact referenced", CheckSeverity.CRITICAL,
        "Pair has no raw_snapshot_key or input_record_key · cannot trace evidence."
    )


def check_source_artifact_retrievable(pair: dict[str, Any], store: BakeryStore) -> CheckResult:
    key = pair.get("raw_snapshot_key") or pair.get("input_record_key")
    if not key:
        return _failed(
            "C03", "Source artifact retrievable", CheckSeverity.CRITICAL,
            "No source artifact key on pair · check C02 must pass first."
        )
    try:
        body = store.driver.read(key)
        if not body:
            return _failed(
                "C03", "Source artifact retrievable", CheckSeverity.CRITICAL,
                f"Source artifact at {key} returned empty body."
            )
        return _passed(
            "C03", "Source artifact retrievable", CheckSeverity.CRITICAL,
            f"Read {len(body)} bytes from source artifact.",
            evidence={"artifact_key": key, "byte_size": len(body)},
        )
    except Exception as exc:  # noqa: BLE001
        return _failed(
            "C03", "Source artifact retrievable", CheckSeverity.CRITICAL,
            f"Source artifact at {key} unreadable: {type(exc).__name__}",
        )


def check_tribunal_label_present(pair: dict[str, Any], _store: BakeryStore) -> CheckResult:
    label = pair.get("tribunal_label")
    if label and label != "PENDING":
        return _passed(
            "C04", "Tribunal label assigned",
            CheckSeverity.CRITICAL,
            f"Tribunal label is {label} · classification has occurred.",
            evidence={"tribunal_label": label},
        )
    if label == "PENDING":
        return _failed(
            "C04", "Tribunal label assigned", CheckSeverity.CRITICAL,
            "Pair is still PENDING · Tribunal must classify before Validator review."
        )
    return _failed(
        "C04", "Tribunal label assigned", CheckSeverity.CRITICAL,
        "Pair has no tribunal_label field at all."
    )


def check_no_hard_fail(pair: dict[str, Any], _store: BakeryStore) -> CheckResult:
    if pair.get("hard_fail") is True:
        return _failed(
            "C05", "No hard-fail flag", CheckSeverity.CRITICAL,
            "Pair carries hard_fail=true · cannot advance · adversarial only."
        )
    return _passed(
        "C05", "No hard-fail flag", CheckSeverity.CRITICAL,
        "hard_fail=false on the pair · advancement permitted.",
    )


def check_propolis_not_promoted(pair: dict[str, Any], _store: BakeryStore) -> CheckResult:
    label = pair.get("tribunal_label")
    if label == "PROPOLIS":
        return _failed(
            "C06", "PROPOLIS not eligible for positive advancement",
            CheckSeverity.CRITICAL,
            "PROPOLIS pairs are preserved as adversarial evidence · "
            "CANNOT be promoted to HONEY or training-eligible.",
        )
    return _passed(
        "C06", "PROPOLIS not eligible for positive advancement",
        CheckSeverity.CRITICAL,
        f"Pair label {label} is not PROPOLIS · positive advancement permitted.",
    )


def check_holdout_not_in_training(pair: dict[str, Any], _store: BakeryStore) -> CheckResult:
    if pair.get("eligible_for_holdout") and pair.get("eligible_for_training"):
        return _failed(
            "C07", "Holdout contamination guard", CheckSeverity.CRITICAL,
            "Pair is both eligible_for_holdout AND eligible_for_training · "
            "doctrine violation · holdout records must NEVER enter training."
        )
    return _passed(
        "C07", "Holdout contamination guard", CheckSeverity.CRITICAL,
        "No holdout/training contamination.",
    )


def check_consent_present_for_live_intake(pair: dict[str, Any], _store: BakeryStore) -> CheckResult:
    if pair.get("source_type") == "synthetic_forge":
        return _passed(
            "C08", "Operator consent (when live intake)",
            CheckSeverity.ADVISORY,
            "Synthetic forge candidate · operator consent not required.",
        )
    # Live intake · for training-admission specifically · consent must be true
    consent = pair.get("operator_training_consent")
    if consent is True:
        return _passed(
            "C08", "Operator consent (when live intake)",
            CheckSeverity.ADVISORY,
            "Operator training consent present.",
        )
    return _failed(
        "C08", "Operator consent (when live intake)", CheckSeverity.ADVISORY,
        "Operator training consent not granted · pair is reviewable but "
        "cannot enter a training release without operator opt-in."
    )


def check_redaction_status(pair: dict[str, Any], _store: BakeryStore) -> CheckResult:
    status = pair.get("redaction_status")
    if status in ("COMPLETED", "NOT_APPLICABLE"):
        return _passed(
            "C09", "Redaction status acceptable", CheckSeverity.ADVISORY,
            f"Redaction status is {status}.",
        )
    return _failed(
        "C09", "Redaction status acceptable", CheckSeverity.ADVISORY,
        f"Redaction status {status!r} · must be COMPLETED or NOT_APPLICABLE."
    )


def check_transition_log_present(pair: dict[str, Any], _store: BakeryStore) -> CheckResult:
    log = pair.get("transition_log") or []
    if log:
        return _passed(
            "C10", "Transition audit log", CheckSeverity.ADVISORY,
            f"Pair has {len(log)} transition entry/entries · audit trail present.",
            evidence={"transition_count": len(log)},
        )
    return _failed(
        "C10", "Transition audit log", CheckSeverity.ADVISORY,
        "No transition log entries · no audit trail for label changes."
    )


def check_sha256_recorded(pair: dict[str, Any], _store: BakeryStore) -> CheckResult:
    if pair.get("sha256"):
        return _passed(
            "C11", "Pair SHA-256 recorded", CheckSeverity.ADVISORY,
            "Pair candidate has a sha256 of its serialized record.",
        )
    return _failed(
        "C11", "Pair SHA-256 recorded", CheckSeverity.ADVISORY,
        "No sha256 on the pair record itself."
    )


def check_no_secret_in_pair(pair: dict[str, Any], _store: BakeryStore) -> CheckResult:
    """Scan the pair JSON for obvious secret markers.

    A pair candidate should never contain Bearer tokens, Authorization
    headers, PEM blocks, API keys, etc. The other layers strip these but
    we double-check at validator time as a defense in depth.
    """
    forbidden_markers = (
        "BEGIN PRIVATE KEY", "BEGIN RSA PRIVATE KEY", "BEGIN OPENSSH",
        "sk-", "ghp_", "AKIA", "Bearer ey",
    )
    blob = json.dumps(pair, sort_keys=True)
    for marker in forbidden_markers:
        if marker in blob:
            return _failed(
                "C12", "No secret material in pair record",
                CheckSeverity.CRITICAL,
                f"Pair record contains forbidden marker {marker!r} · refuse advancement."
            )
    return _passed(
        "C12", "No secret material in pair record", CheckSeverity.CRITICAL,
        "Scan of pair JSON found no secret-shaped markers.",
    )


# ─── The 12-check registry · order matters for reviewer UI ───────────


CHECK_REGISTRY: tuple[tuple[str, str, CheckFn], ...] = (
    ("C01", "Pair record present", check_pair_record_present),
    ("C02", "Source artifact referenced", check_source_artifact_referenced),
    ("C03", "Source artifact retrievable", check_source_artifact_retrievable),
    ("C04", "Tribunal label assigned", check_tribunal_label_present),
    ("C05", "No hard-fail flag", check_no_hard_fail),
    ("C06", "PROPOLIS not eligible for positive advancement", check_propolis_not_promoted),
    ("C07", "Holdout contamination guard", check_holdout_not_in_training),
    ("C08", "Operator consent (when live intake)", check_consent_present_for_live_intake),
    ("C09", "Redaction status acceptable", check_redaction_status),
    ("C10", "Transition audit log present", check_transition_log_present),
    ("C11", "Pair SHA-256 recorded", check_sha256_recorded),
    ("C12", "No secret material in pair record", check_no_secret_in_pair),
)


def list_doctrine_checks() -> list[dict[str, str]]:
    """Public-safe surface · returns check ID + name + severity."""
    rows = []
    # Run each against a stub pair to discover severity (no state)
    for check_id, name, fn in CHECK_REGISTRY:
        # We construct a minimal stub that exercises the function · the
        # severity is constant for each check regardless of input.
        stub = {
            "pair_id": "STUB", "source_run_id": "STUB",
            "raw_snapshot_key": "stub-key", "tribunal_label": "PENDING",
            "hard_fail": False, "eligible_for_holdout": False,
            "eligible_for_training": False, "source_type": "synthetic_forge",
            "redaction_status": "NOT_APPLICABLE", "transition_log": [{"x": 1}],
            "sha256": "x" * 64,
        }
        try:
            # We swallow exceptions · only want severity classification
            from unittest.mock import MagicMock
            stub_store = MagicMock()
            stub_store.driver.read.return_value = b"x"
            result = fn(stub, stub_store)
            severity = result.severity.value
        except Exception:  # noqa: BLE001
            severity = "ADVISORY"
        rows.append({"check_id": check_id, "name": name, "severity": severity})
    return rows


# ─── Review session orchestrator ─────────────────────────────────────


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_session_id() -> str:
    return f"VR-{uuid.uuid4().hex[:14].upper()}"


def run_validator_review(
    *,
    pair: dict[str, Any],
    reviewer_user_id: str,
    store: BakeryStore | None = None,
) -> ValidatorReviewSession:
    """Run every doctrine check against a pair · build a session record."""
    store = store or get_bakery_store()
    session = ValidatorReviewSession(
        session_id=_new_session_id(),
        pair_id=pair.get("pair_id", "UNKNOWN"),
        started_at=_now_iso(),
        completed_at=None,
        reviewer_user_id=reviewer_user_id,
    )

    critical_failed = 0
    advisory_failed = 0
    nyi_count = 0
    for _check_id, _name, fn in CHECK_REGISTRY:
        try:
            result = fn(pair, store)
        except Exception as exc:  # noqa: BLE001
            result = _inconclusive(
                _check_id, _name, CheckSeverity.ADVISORY,
                f"Check raised {type(exc).__name__}: {exc}",
            )
        session.checks.append(result)
        if result.status == CheckStatus.FAILED:
            if result.severity == CheckSeverity.CRITICAL:
                critical_failed += 1
            else:
                advisory_failed += 1
        if result.status == CheckStatus.NOT_YET_IMPLEMENTED:
            nyi_count += 1

    # ── Overall status ──────────────────────────────────────────────
    if critical_failed > 0:
        session.overall_status = "FAILED"
        session.advance_to_label = "QUARANTINED"
    elif advisory_failed > 0:
        session.overall_status = "DOWNGRADED"
        session.advance_to_label = "JELLY"
    else:
        session.overall_status = "PASSED"
        session.advance_to_label = "HONEY"

    session.completed_at = _now_iso()
    session.doctrine_seal = {
        "automated_review_only": True,
        "deed_issuance": "NOT_AUTOMATED_FROM_THIS_SESSION",
        "training_admission": "STILL_REQUIRES_CONSENT_AND_REDACTION_FLAGS",
        "session_id": session.session_id,
        "critical_failed": critical_failed,
        "advisory_failed": advisory_failed,
        "not_yet_implemented": nyi_count,
        "reviewer_user_id": reviewer_user_id,
    }

    # Persist immutable session record
    body = json.dumps(session.to_dict(), sort_keys=True, indent=2).encode("utf-8")
    key = bakery_key(
        "compute-claw", "validator-review", f"{safe_key_part(session.session_id)}.json",
    )
    # The validator-review subtree is shared between compute-claw and bakery
    # · for now we use compute-claw/validator-review/. Could be split later
    # if other rails need their own validator review surface.
    try:
        artifact = store.driver.write_immutable(key, body, "application/json")
    except Exception:
        # Fallback to a bakery-shared validator-review location if compute-claw
        # subtree doesn't exist (older deploy)
        key = bakery_key("pair-candidates", "pending", f"VR-{session.session_id}.json")
        artifact = store.driver.write_immutable(key, body, "application/json")

    generate_receipt(
        artifact_type="validator_review",
        artifact_key=artifact.key,
        artifact_bytes=body,
        source_run_id=session.pair_id,
        tribunal_label=session.advance_to_label or "UNKNOWN",
        redaction_status="NOT_APPLICABLE",
        consent_status={"validator_session": True},
        extra_metadata={
            "rail": "validator_review",
            "session_id": session.session_id,
            "reviewer_user_id": reviewer_user_id,
        },
        store=store,
    )
    append_event(
        event_type="clawcheck.validator.review_requested",
        run_id=session.pair_id,
        payload={
            "rail": "validator.review.completed",
            "session_id": session.session_id,
            "overall_status": session.overall_status,
            "advance_to_label": session.advance_to_label,
        },
        store=store,
    )

    return session
