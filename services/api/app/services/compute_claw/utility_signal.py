"""UtilitySignal · rental/income evidence attachment.

Per the build spec: do NOT scrape Vast.ai or invent API capabilities.
Three statuses only:

  · OPERATOR_SUPPLIED_UNVERIFIED       · operator pasted figures · no receipt
  · DEFENDABLE_FLEET_RECEIPT_VERIFIED  · receipt from Defendable's own fleet
  · NOT_SUPPLIED                       · nothing attached yet

Doctrine guarantees enforced:
  · Operator-supplied rates/durations WITHOUT a receipt are marked
    unverified · verified_by_defendable stays False
  · eBay asking-price evidence is NEVER income evidence · this module
    refuses to attach a record whose source is "EBAY_ASKING_PRICE"
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


UTILITY_STATUSES: tuple[str, ...] = (
    "NOT_SUPPLIED",
    "OPERATOR_SUPPLIED_UNVERIFIED",
    "DEFENDABLE_FLEET_RECEIPT_VERIFIED",
)

ALLOWED_UTILITY_SOURCES: tuple[str, ...] = (
    "VAST_AI",
    "RUNPOD",
    "LAMBDA_LABS",
    "DEFENDABLE_FLEET",
    "OPERATOR_OWN_DEPLOYMENT",
)


class UtilityAttachError(ValueError):
    pass


@dataclass
class UtilityEvidence:
    utility_evidence_id: str
    asset_intake_id: str
    utility_source: str
    evidence_status: str
    rental_hourly_rate: float | None
    rental_duration_hours: float | None
    gross_revenue_observed: float | None
    receipt_path: str | None
    verified_by_defendable: bool
    captured_at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _new_evidence_id() -> str:
    return f"DUTIL-{uuid.uuid4().hex[:14].upper()}"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def attach_utility_evidence(
    *,
    asset_intake_id: str,
    utility_source: str,
    rental_hourly_rate: float | None = None,
    rental_duration_hours: float | None = None,
    gross_revenue_observed: float | None = None,
    receipt_path: str | None = None,
    fleet_verified: bool = False,
    store: BakeryStore | None = None,
) -> tuple[UtilityEvidence, dict[str, Any]]:
    """Attach a utility evidence record. Returns the record + envelope.

    Rules:
      · utility_source must be in ALLOWED_UTILITY_SOURCES
      · EBAY_ASKING_PRICE source is explicitly REFUSED · listing != income
      · fleet_verified=True is only honored for source=DEFENDABLE_FLEET
        with a receipt_path · otherwise the evidence stays UNVERIFIED
    """
    if not asset_intake_id or not isinstance(asset_intake_id, str):
        raise UtilityAttachError("asset_intake_id is required")
    if utility_source.upper() in ("EBAY_ASKING_PRICE", "EBAY_BROWSE", "EBAY"):
        raise UtilityAttachError(
            "eBay asking-price evidence is NOT income evidence · refuse"
        )
    if utility_source not in ALLOWED_UTILITY_SOURCES:
        raise UtilityAttachError(
            f"utility_source must be one of {list(ALLOWED_UTILITY_SOURCES)}"
        )

    # Determine status
    has_figures = any(
        v is not None for v in (
            rental_hourly_rate, rental_duration_hours, gross_revenue_observed,
        )
    )

    if not has_figures and not receipt_path:
        status = "NOT_SUPPLIED"
        verified = False
    elif fleet_verified and receipt_path and utility_source == "DEFENDABLE_FLEET":
        status = "DEFENDABLE_FLEET_RECEIPT_VERIFIED"
        verified = True
    else:
        status = "OPERATOR_SUPPLIED_UNVERIFIED"
        verified = False

    evidence = UtilityEvidence(
        utility_evidence_id=_new_evidence_id(),
        asset_intake_id=asset_intake_id,
        utility_source=utility_source,
        evidence_status=status,
        rental_hourly_rate=rental_hourly_rate,
        rental_duration_hours=rental_duration_hours,
        gross_revenue_observed=gross_revenue_observed,
        receipt_path=receipt_path,
        verified_by_defendable=verified,
        captured_at=_now_iso(),
    )

    store = store or get_bakery_store()
    body = json.dumps(evidence.to_dict(), sort_keys=True, indent=2).encode("utf-8")
    key = bakery_key(
        "compute-claw", "utility-evidence",
        f"{safe_key_part(evidence.utility_evidence_id)}.json",
    )
    artifact = store.driver.write_immutable(key, body, "application/json")

    receipt = generate_receipt(
        artifact_type="pair_candidate",
        artifact_key=artifact.key,
        artifact_bytes=body,
        source_run_id=asset_intake_id,
        tribunal_label="VERIFIED" if verified else "UNVERIFIED",
        redaction_status="NOT_APPLICABLE",
        consent_status={"utility_evidence_pointer": True},
        extra_metadata={
            "rail": "compute_claw.utility_evidence",
            "utility_evidence_id": evidence.utility_evidence_id,
            "asset_intake_id": asset_intake_id,
            "utility_source": utility_source,
            "status": status,
        },
        store=store,
    )
    append_event(
        event_type="clawcheck.receipt.generated",
        run_id=asset_intake_id,
        payload={
            "rail": "computeclaw.utility_evidence.attached",
            "utility_evidence_id": evidence.utility_evidence_id,
            "utility_source": utility_source,
            "status": status,
            "receipt_id": receipt["receipt_id"],
        },
        store=store,
    )

    envelope = {
        "utility_evidence_id": evidence.utility_evidence_id,
        "artifact_key": artifact.key,
        "artifact_sha256": artifact.sha256,
        "receipt_id": receipt["receipt_id"],
        "status": status,
        "verified_by_defendable": verified,
    }
    return evidence, envelope
