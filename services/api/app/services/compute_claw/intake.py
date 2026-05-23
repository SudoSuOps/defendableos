"""ComputeClaw intake · creates immutable owner-attested asset record.

The intake step DOES NOT issue a value number. It captures:
  · what the owner says they own
  · what outcome they want (sell · insure · finance · document · rent · ...)
  · which evidence already exists (photos · serial-hash · benchmark · etc)
  · their consent flags

It then writes the raw intake immutably under
`compute-claw/raw-intakes/<intake_id>.json`, emits a compliance event,
and returns a readiness snapshot.

The readiness snapshot tells the operator what evidence is STILL needed
before the Proof Pack can advance — it never substitutes for that work.
"""
from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any

from app.services.claw_bakery.bakery_storage import (
    BakeryStore,
    bakery_key,
    get_bakery_store,
    safe_key_part,
)
from app.services.claw_bakery.bakery_events import append_event
from app.services.claw_bakery.receipts import generate_receipt
from app.services.compute_claw.categories import (
    ASSET_CATEGORIES,
    ASSET_TYPES,
    is_known_asset_category,
    is_known_asset_type,
)


# ─── Outcome catalogue ───────────────────────────────────────────────


SUPPORTED_OUTCOMES: tuple[str, ...] = (
    "sell",
    "insure",
    "finance",
    "document",
    "rent",
    "benchmark",
    "prepare_proof_of_value_package",
)


READINESS_STATUSES: tuple[str, ...] = (
    "INTAKE_ONLY",
    "MARKET_EVIDENCE_COLLECTED",
    "BENCHMARK_REQUIRED",
    "UTILITY_EVIDENCE_OPTIONAL",
    "READY_FOR_VALIDATOR_REVIEW",
    "DEED_ELIGIBILITY_REVIEW_REQUIRED",
)


# ─── Errors ──────────────────────────────────────────────────────────


class IntakeValidationError(ValueError):
    pass


# ─── Dataclasses ─────────────────────────────────────────────────────


@dataclass
class IntakeEvidenceSupplied:
    photos: bool = False
    serial_hash: bool = False
    benchmark_receipt: bool = False
    purchase_receipt: bool = False
    rental_receipts: bool = False


@dataclass
class IntakeConsent:
    store_for_review: bool = True
    allow_public_redacted_demo: bool = False


@dataclass
class ComputeIntake:
    asset_intake_id: str
    asset_owner_attested: bool
    asset_type: str
    asset_category: str
    manufacturer: str
    model_name: str
    vram_gb: int | None
    quantity: int
    condition_claimed: str
    intended_outcome: str
    use_case: list[str]
    evidence_supplied: IntakeEvidenceSupplied
    operator_notes: str
    consent: IntakeConsent
    captured_at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ReadinessSnapshot:
    asset_intake_id: str
    asset_summary: str
    intended_outcome: str
    evidence_supplied_summary: str
    benchmark_status: str
    observed_market_eligible: bool
    utility_evidence_status: str
    readiness_status: str
    recommended_next_steps: list[str]
    doctrine_disclaimer: str


# ─── Factory + validation ────────────────────────────────────────────


def _new_intake_id() -> str:
    return f"DCOMP-INTAKE-{uuid.uuid4().hex[:12].upper()}"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _validate_payload(payload: dict[str, Any]) -> None:
    if not isinstance(payload, dict):
        raise IntakeValidationError("payload must be a JSON object")

    if not payload.get("asset_owner_attested"):
        raise IntakeValidationError(
            "asset_owner_attested must be true · operator must confirm "
            "they have rights to describe the asset"
        )

    asset_type = payload.get("asset_type")
    if not is_known_asset_type(asset_type or ""):
        raise IntakeValidationError(
            f"asset_type must be one of {list(ASSET_TYPES)}"
        )

    asset_category = payload.get("asset_category")
    if not is_known_asset_category(asset_category or ""):
        raise IntakeValidationError(
            f"asset_category must be one of {list(ASSET_CATEGORIES.keys())}"
        )

    manufacturer = payload.get("manufacturer")
    if not manufacturer or not isinstance(manufacturer, str):
        raise IntakeValidationError("manufacturer is required")

    model_name = payload.get("model_name")
    if not model_name or not isinstance(model_name, str):
        raise IntakeValidationError("model_name is required")

    quantity = payload.get("quantity", 1)
    if not isinstance(quantity, int) or quantity < 1:
        raise IntakeValidationError("quantity must be a positive integer")

    intended_outcome = payload.get("intended_outcome")
    if intended_outcome not in SUPPORTED_OUTCOMES:
        raise IntakeValidationError(
            f"intended_outcome must be one of {list(SUPPORTED_OUTCOMES)}"
        )

    use_case = payload.get("use_case") or []
    if not isinstance(use_case, list):
        raise IntakeValidationError("use_case must be a list of strings")

    vram_gb = payload.get("vram_gb")
    if vram_gb is not None:
        if not isinstance(vram_gb, int) or vram_gb < 0 or vram_gb > 4096:
            raise IntakeValidationError("vram_gb must be a non-negative integer ≤4096")


def _build_intake(payload: dict[str, Any]) -> ComputeIntake:
    ev = payload.get("evidence_supplied") or {}
    consent = payload.get("consent") or {}
    return ComputeIntake(
        asset_intake_id=_new_intake_id(),
        asset_owner_attested=bool(payload["asset_owner_attested"]),
        asset_type=payload["asset_type"],
        asset_category=payload["asset_category"],
        manufacturer=payload["manufacturer"],
        model_name=payload["model_name"],
        vram_gb=payload.get("vram_gb"),
        quantity=int(payload.get("quantity", 1)),
        condition_claimed=str(payload.get("condition_claimed") or "Unknown"),
        intended_outcome=payload["intended_outcome"],
        use_case=list(payload.get("use_case") or []),
        evidence_supplied=IntakeEvidenceSupplied(
            photos=bool(ev.get("photos", False)),
            serial_hash=bool(ev.get("serial_hash", False)),
            benchmark_receipt=bool(ev.get("benchmark_receipt", False)),
            purchase_receipt=bool(ev.get("purchase_receipt", False)),
            rental_receipts=bool(ev.get("rental_receipts", False)),
        ),
        operator_notes=str(payload.get("operator_notes") or "")[:4000],
        consent=IntakeConsent(
            store_for_review=bool(consent.get("store_for_review", True)),
            allow_public_redacted_demo=bool(
                consent.get("allow_public_redacted_demo", False)
            ),
        ),
        captured_at=_now_iso(),
    )


# ─── Readiness snapshot ──────────────────────────────────────────────


_DISCLAIMER = (
    "ComputeClaw captures owner-attested intake only. "
    "Observed eBay active listings are asking-price evidence, NOT verified "
    "sold comps. A benchmark receipt is required for any Defendable-tested "
    "condition claim. No final value opinion or deed is issued by intake."
)


def _build_snapshot(intake: ComputeIntake) -> ReadinessSnapshot:
    ev = intake.evidence_supplied
    benchmark_status = (
        "Benchmark receipt provided (pending verification)"
        if ev.benchmark_receipt else "Not yet supplied"
    )
    utility_evidence_status = (
        "Rental/income receipts provided (pending verification)"
        if ev.rental_receipts else "Not yet supplied (optional)"
    )
    supplied = [
        name for name, present in (
            ("photos", ev.photos),
            ("serial-hash", ev.serial_hash),
            ("benchmark receipt", ev.benchmark_receipt),
            ("purchase receipt", ev.purchase_receipt),
            ("rental receipts", ev.rental_receipts),
        ) if present
    ]
    evidence_summary = ", ".join(supplied) if supplied else "owner description only"

    # Recommended next steps · ordered by what's missing
    steps: list[str] = []
    if not ev.photos:
        steps.append("Capture machine identity evidence (photos · serial-hash)")
    if not ev.benchmark_receipt:
        steps.append("Run Defendable hardware benchmark")
    steps.append("Gather observed-market asking-price evidence (eBay Browse)")
    if not ev.rental_receipts:
        steps.append("Add verified rental/utility records if available")
    steps.append("Submit for AIOV draft review")
    steps.append("Validator approval required before deed eligibility")

    readiness = "INTAKE_ONLY"

    asset_summary = f"{intake.manufacturer} {intake.model_name}"
    if intake.vram_gb is not None:
        asset_summary = f"{asset_summary} ({intake.vram_gb}GB VRAM)"
    if intake.quantity > 1:
        asset_summary = f"{asset_summary} × {intake.quantity}"

    return ReadinessSnapshot(
        asset_intake_id=intake.asset_intake_id,
        asset_summary=asset_summary,
        intended_outcome=intake.intended_outcome,
        evidence_supplied_summary=evidence_summary,
        benchmark_status=benchmark_status,
        observed_market_eligible=True,
        utility_evidence_status=utility_evidence_status,
        readiness_status=readiness,
        recommended_next_steps=steps,
        doctrine_disclaimer=_DISCLAIMER,
    )


# ─── Public entry point ──────────────────────────────────────────────


def submit_intake(
    payload: dict[str, Any],
    *,
    store: BakeryStore | None = None,
) -> tuple[ComputeIntake, ReadinessSnapshot, dict[str, Any]]:
    """Validate payload · write raw intake immutably · return (intake,
    snapshot, bakery_envelope). The bakery_envelope describes the stored
    artifact + receipt + event for downstream wiring; the snapshot is the
    operator-facing readiness summary."""
    _validate_payload(payload)
    intake = _build_intake(payload)
    store = store or get_bakery_store()

    # Write raw intake immutably
    body_dict = intake.to_dict()
    body = json.dumps(body_dict, sort_keys=True, indent=2).encode("utf-8")
    key = bakery_key(
        "compute-claw", "raw-intakes",
        f"{safe_key_part(intake.asset_intake_id)}.json",
    )
    artifact = store.driver.write_immutable(key, body, "application/json")

    # SHA-256 receipt over the raw bytes
    receipt = generate_receipt(
        artifact_type="intake",
        artifact_key=artifact.key,
        artifact_bytes=body,
        source_run_id=intake.asset_intake_id,
        tribunal_label="N/A",
        redaction_status="NOT_APPLICABLE",
        consent_status=asdict(intake.consent),
        extra_metadata={
            "rail": "compute_claw",
            "asset_type": intake.asset_type,
            "asset_category": intake.asset_category,
            "intended_outcome": intake.intended_outcome,
        },
        store=store,
    )

    # Compliance event · standard bakery channel
    event_payload = {
        "asset_intake_id": intake.asset_intake_id,
        "asset_type": intake.asset_type,
        "asset_category": intake.asset_category,
        "intended_outcome": intake.intended_outcome,
        "artifact_key": artifact.key,
        "artifact_sha256": artifact.sha256,
        "receipt_id": receipt["receipt_id"],
        "rail": "compute_claw.intake.completed",
    }
    event = append_event(
        event_type="clawcheck.intake.completed",
        run_id=intake.asset_intake_id,
        payload=event_payload,
        store=store,
    )

    snapshot = _build_snapshot(intake)
    return intake, snapshot, {
        "artifact_key": artifact.key,
        "artifact_sha256": artifact.sha256,
        "receipt_id": receipt["receipt_id"],
        "event_id": event["event_id"],
    }
