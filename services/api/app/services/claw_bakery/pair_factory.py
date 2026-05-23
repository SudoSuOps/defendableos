"""Claw Bakery Pair Factory · agent-domain pair candidates.

Distinct from services/pair_factory.py (which is goods-domain). This
module models the pair-candidate that flows from a completed ClawCheck
snapshot → Validator → Tribunal → Honey/Jelly/Propolis.

Hard doctrine guarantees enforced at function boundaries:

  · A live-intake pair candidate is NEVER training-eligible by default.
    eligible_for_training requires:
      - tribunal_label ∈ {HONEY, JELLY_REPAIRED_TO_HONEY}
      - redaction_status == COMPLETED
      - consent.allow_deidentified_training_use == True
      - validator_status == PASSED

  · PROPOLIS is NEVER training-eligible as a positive label.
    It can become an adversarial evaluation candidate (a "what bad
    looks like" example) but only after review · never as a Honey
    target.

  · A synthetic candidate from ClawForge is created with synthetic=True
    AND tribunal_label=PENDING · it cannot auto-promote to Honey.

  · Holdout candidates are sealed · once marked eligible_for_holdout,
    they may NEVER be marked eligible_for_training (contamination ban).

Storage: pair candidates are stored as JSON in the bakery vault.
The `pair-candidates/<label>/<pair_id>.json` key is moved by setting
the tribunal_label + re-writing (the bucket is part of the key).
"""
from __future__ import annotations

import enum
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal

from app.services.claw_bakery.bakery_storage import BakeryStore, get_bakery_store
from app.services.claw_bakery.bakery_events import append_event


class TribunalLabel(str, enum.Enum):
    PENDING = "PENDING"
    HONEY = "HONEY"
    JELLY = "JELLY"
    JELLY_REPAIRED_TO_HONEY = "JELLY_REPAIRED_TO_HONEY"
    PROPOLIS = "PROPOLIS"
    QUARANTINED = "QUARANTINED"


class RedactionStatus(str, enum.Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class ValidatorStatus(str, enum.Enum):
    PENDING = "PENDING"
    UNDER_REVIEW = "UNDER_REVIEW"
    PASSED = "PASSED"
    FAILED = "FAILED"


_BUCKET_FOR_LABEL: dict[TribunalLabel, str] = {
    TribunalLabel.PENDING: "pending",
    TribunalLabel.HONEY: "honey",
    TribunalLabel.JELLY: "jelly",
    TribunalLabel.JELLY_REPAIRED_TO_HONEY: "jelly-repaired",
    TribunalLabel.PROPOLIS: "propolis-failures",
    TribunalLabel.QUARANTINED: "quarantined",
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class PairCandidate:
    pair_id: str
    source_run_id: str
    source_type: Literal["live_intake", "synthetic_forge"]
    synthetic: bool
    agent_name: str | None
    domain: str
    risk_class: str
    input_record_key: str | None
    raw_snapshot_key: str | None
    tribunal_label: str = TribunalLabel.PENDING.value
    validator_status: str = ValidatorStatus.PENDING.value
    redaction_status: str = RedactionStatus.PENDING.value
    operator_training_consent: bool = False
    operator_evaluation_consent: bool = False
    eligible_for_training: bool = False
    eligible_for_evaluation: bool = False
    eligible_for_holdout: bool = False
    hard_fail: bool = False
    sha256: str | None = None
    created_at: str = field(default_factory=_now)
    last_transition: str = field(default_factory=_now)
    transition_log: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class PairFactoryError(ValueError):
    pass


def _new_pair_id() -> str:
    return f"DCLAW-PAIR-{uuid.uuid4().hex[:10].upper()}"


def create_pair_candidate_from_snapshot(
    *,
    source_run_id: str,
    snapshot: dict[str, Any],
    input_record_key: str | None,
    raw_snapshot_key: str | None,
    operator_consent: dict[str, bool] | None = None,
    store: BakeryStore | None = None,
) -> PairCandidate:
    """Create a PENDING pair candidate from a completed ClawCheck snapshot."""
    store = store or get_bakery_store()
    consent = operator_consent or {}
    risk = snapshot.get("risk") or {}
    captured = snapshot.get("captured") or {}
    pair = PairCandidate(
        pair_id=_new_pair_id(),
        source_run_id=source_run_id,
        source_type="live_intake",
        synthetic=False,
        agent_name=captured.get("agent_name"),
        domain=_classify_domain(captured.get("worker_kind")),
        risk_class=risk.get("rule_id") or risk.get("risk_class") or "UNCLASSIFIED",
        input_record_key=input_record_key,
        raw_snapshot_key=raw_snapshot_key,
        tribunal_label=TribunalLabel.PENDING.value,
        validator_status=ValidatorStatus.PENDING.value,
        redaction_status=RedactionStatus.PENDING.value,
        operator_training_consent=bool(consent.get("allow_deidentified_training_use", False)),
        operator_evaluation_consent=bool(consent.get("allow_evaluation_use", False)),
        eligible_for_training=False,
        eligible_for_evaluation=False,
        eligible_for_holdout=False,
        hard_fail=False,
    )
    _persist(pair, store)
    append_event(
        event_type="clawcheck.pair_candidate.created",
        run_id=source_run_id,
        payload={
            "pair_id": pair.pair_id,
            "source_type": pair.source_type,
            "domain": pair.domain,
            "risk_class": pair.risk_class,
            "tribunal_label": pair.tribunal_label,
        },
        store=store,
    )
    return pair


def create_synthetic_candidate(
    *,
    source_run_id: str,
    agent_name: str,
    domain: str,
    risk_class: str,
    proposed_input: dict[str, Any],
    proposed_target: dict[str, Any],
    store: BakeryStore | None = None,
) -> PairCandidate:
    """Create a synthetic ClawForge candidate · always PENDING + synthetic."""
    store = store or get_bakery_store()
    pair = PairCandidate(
        pair_id=_new_pair_id(),
        source_run_id=source_run_id,
        source_type="synthetic_forge",
        synthetic=True,
        agent_name=agent_name,
        domain=domain,
        risk_class=risk_class,
        input_record_key=None,
        raw_snapshot_key=None,
        tribunal_label=TribunalLabel.PENDING.value,
        validator_status=ValidatorStatus.PENDING.value,
        redaction_status=RedactionStatus.NOT_APPLICABLE.value,
        operator_training_consent=False,
        operator_evaluation_consent=False,
        eligible_for_training=False,
        eligible_for_evaluation=False,
        eligible_for_holdout=False,
        hard_fail=False,
    )
    # Embed synthetic payload directly in the candidate
    pair.transition_log.append({
        "at": _now(),
        "kind": "synthetic_created",
        "input": proposed_input,
        "target": proposed_target,
    })
    _persist(pair, store)
    append_event(
        event_type="clawforge.candidate.generated",
        run_id=source_run_id,
        payload={
            "pair_id": pair.pair_id,
            "agent_name": agent_name,
            "domain": domain,
            "risk_class": risk_class,
            "synthetic": True,
        },
        store=store,
    )
    return pair


def assign_tribunal_label(
    pair: PairCandidate,
    *,
    label: TribunalLabel,
    reason: str,
    store: BakeryStore | None = None,
) -> PairCandidate:
    """Move a pair candidate to a new Tribunal label · re-persists under the
    label's bucket key. PROPOLIS may not be flipped back to HONEY directly ·
    a JELLY_REPAIRED_TO_HONEY transition exists for repairs.
    """
    store = store or get_bakery_store()
    if pair.tribunal_label == TribunalLabel.PROPOLIS.value and label == TribunalLabel.HONEY:
        raise PairFactoryError(
            f"pair {pair.pair_id}: PROPOLIS cannot be flipped to HONEY · "
            f"adversarial-eval lane only"
        )
    if label == TribunalLabel.PROPOLIS:
        pair.hard_fail = True
    pair.tribunal_label = label.value
    pair.last_transition = _now()
    pair.transition_log.append({
        "at": pair.last_transition,
        "kind": "tribunal_label_assigned",
        "label": label.value,
        "reason": reason,
    })
    # Recompute eligibility after every label change
    _recompute_eligibility(pair)
    _persist(pair, store)
    return pair


def set_validator_status(
    pair: PairCandidate,
    *,
    status: ValidatorStatus,
    reason: str,
    store: BakeryStore | None = None,
) -> PairCandidate:
    store = store or get_bakery_store()
    pair.validator_status = status.value
    pair.last_transition = _now()
    pair.transition_log.append({
        "at": pair.last_transition,
        "kind": "validator_status",
        "status": status.value,
        "reason": reason,
    })
    _recompute_eligibility(pair)
    _persist(pair, store)
    return pair


def set_redaction_status(
    pair: PairCandidate,
    *,
    status: RedactionStatus,
    reason: str,
    store: BakeryStore | None = None,
) -> PairCandidate:
    store = store or get_bakery_store()
    pair.redaction_status = status.value
    pair.last_transition = _now()
    pair.transition_log.append({
        "at": pair.last_transition,
        "kind": "redaction_status",
        "status": status.value,
        "reason": reason,
    })
    _recompute_eligibility(pair)
    _persist(pair, store)
    return pair


def seal_as_holdout(
    pair: PairCandidate,
    *,
    reason: str,
    store: BakeryStore | None = None,
) -> PairCandidate:
    """Mark this candidate as a sealed holdout · forbidden from training forever.

    Doctrine: a holdout can never enter a training release. Once sealed,
    eligible_for_training is locked False · attempts to flip it raise
    PairFactoryError.
    """
    store = store or get_bakery_store()
    pair.eligible_for_holdout = True
    pair.eligible_for_training = False
    pair.last_transition = _now()
    pair.transition_log.append({
        "at": pair.last_transition,
        "kind": "sealed_as_holdout",
        "reason": reason,
    })
    _persist(pair, store)
    return pair


def assert_can_enter_training_release(pair: PairCandidate) -> None:
    """Doctrine gate · raises unless every condition for training is met.

    Used by dataset-release assembly. PROPOLIS, holdouts, and any
    unconsented or unredacted candidate must raise.
    """
    if pair.eligible_for_holdout:
        raise PairFactoryError(
            f"pair {pair.pair_id} is a sealed holdout · cannot enter training release"
        )
    if not pair.eligible_for_training:
        raise PairFactoryError(
            f"pair {pair.pair_id} eligible_for_training=False · refuse export"
        )
    if pair.tribunal_label not in (TribunalLabel.HONEY.value, TribunalLabel.JELLY_REPAIRED_TO_HONEY.value):
        raise PairFactoryError(
            f"pair {pair.pair_id} tribunal_label={pair.tribunal_label} · "
            f"only HONEY or JELLY_REPAIRED_TO_HONEY may train"
        )
    if pair.validator_status != ValidatorStatus.PASSED.value:
        raise PairFactoryError(
            f"pair {pair.pair_id} validator_status={pair.validator_status} · must be PASSED"
        )
    if pair.redaction_status != RedactionStatus.COMPLETED.value:
        raise PairFactoryError(
            f"pair {pair.pair_id} redaction_status={pair.redaction_status} · must be COMPLETED"
        )
    if pair.source_type == "live_intake" and not pair.operator_training_consent:
        raise PairFactoryError(
            f"pair {pair.pair_id} is a live intake without operator training consent · refuse"
        )


# ─── Internals ────────────────────────────────────────────────────────


def _classify_domain(worker_kind: str | None) -> str:
    if not worker_kind:
        return "unspecified"
    mapping = {
        "Business Agent": "business_agent",
        "Coding Agent": "coding_ops_agent",
        "Sales / Support Agent": "refund_agent",
        "Personal Assistant": "personal_assistant",
        "Local File Agent": "local_file_agent",
        "Custom Workflow Agent": "custom_workflow_agent",
    }
    return mapping.get(worker_kind, "unspecified")


def _recompute_eligibility(pair: PairCandidate) -> None:
    """Single source of truth for eligibility booleans."""
    if pair.eligible_for_holdout:
        pair.eligible_for_training = False
        # Holdouts MAY still be eligible_for_evaluation in evaluation-only mode
        # (sealed but referenced) · we don't force it false here.
        return

    is_honey_like = pair.tribunal_label in (
        TribunalLabel.HONEY.value,
        TribunalLabel.JELLY_REPAIRED_TO_HONEY.value,
    )
    is_propolis = pair.tribunal_label == TribunalLabel.PROPOLIS.value
    validator_ok = pair.validator_status == ValidatorStatus.PASSED.value
    redaction_ok = pair.redaction_status == RedactionStatus.COMPLETED.value

    if is_propolis:
        # PROPOLIS is never a positive training target.
        pair.eligible_for_training = False
        # Adversarial-evaluation eligibility is set explicitly by an
        # admin action (not here).
        return

    if pair.source_type == "live_intake":
        pair.eligible_for_training = bool(
            is_honey_like
            and validator_ok
            and redaction_ok
            and pair.operator_training_consent
        )
        pair.eligible_for_evaluation = bool(
            is_honey_like
            and validator_ok
            and pair.operator_evaluation_consent
        )
    else:
        # Synthetic Forge candidates do not require operator consent
        # (no live PII) but still require Tribunal + Validator approval
        # before training admission.
        pair.eligible_for_training = bool(is_honey_like and validator_ok)
        pair.eligible_for_evaluation = bool(is_honey_like and validator_ok)


def _persist(pair: PairCandidate, store: BakeryStore) -> None:
    bucket = _BUCKET_FOR_LABEL[TribunalLabel(pair.tribunal_label)]
    artifact = store.put_pair_candidate(
        pair_id=pair.pair_id,
        bucket=bucket,  # type: ignore[arg-type]
        payload=pair.to_dict(),
    )
    pair.sha256 = artifact.sha256
