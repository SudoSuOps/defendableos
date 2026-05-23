"""ComputeClaw public + admin endpoints.

Public:
  POST /api/v1/compute-claw/intake               · public · creates compute intake
  GET  /api/v1/compute-claw/categories            · public · returns the catalogue
  GET  /api/v1/compute-claw/readiness-statuses    · public · returns the AIOV statuses

Admin (X-Ebay-Admin-Token gated · same pattern as admin_ebay):
  POST /api/v1/compute-claw/admin/market-observations/ebay/search
       · MarketScout · runs an eBay Browse observation batch
  POST /api/v1/compute-claw/admin/benchmark-evidence/attach
       · BenchInspector · attaches a benchmark-evidence pointer
  POST /api/v1/compute-claw/admin/utility-evidence/attach
       · UtilitySignal · attaches a utility-evidence pointer
  POST /api/v1/compute-claw/admin/aiov-draft/compose
       · ValueComposer · builds a draft AIOV Proof Pack
"""
from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Header, HTTPException, status
from pydantic import BaseModel, Field

from app.core.config import get_settings
from app.services.compute_claw.bench_inspector import (
    BenchmarkAttachError,
    attach_benchmark_evidence,
)
from app.services.compute_claw.categories import (
    ASSET_CATEGORIES,
    ASSET_TYPES,
)
from app.services.compute_claw.intake import (
    IntakeValidationError,
    READINESS_STATUSES,
    SUPPORTED_OUTCOMES,
    submit_intake,
)
from app.services.compute_claw.marketscout import (
    MarketScoutDisabled,
    collect_observations,
    safe_summarize_batch,
)
from app.services.compute_claw.utility_signal import (
    UtilityAttachError,
    attach_utility_evidence,
)
from app.services.compute_claw.value_composer import compose_draft


_log = logging.getLogger("api.compute_claw")

router = APIRouter(prefix="/compute-claw", tags=["compute-claw"])


# ─── Public · intake ─────────────────────────────────────────────────


class EvidenceSuppliedIn(BaseModel):
    photos: bool = False
    serial_hash: bool = False
    benchmark_receipt: bool = False
    purchase_receipt: bool = False
    rental_receipts: bool = False


class ConsentIn(BaseModel):
    store_for_review: bool = True
    allow_public_redacted_demo: bool = False


class ComputeIntakeIn(BaseModel):
    asset_owner_attested: bool = Field(...)
    asset_type: str = Field(..., max_length=80)
    asset_category: str = Field(..., max_length=80)
    manufacturer: str = Field(..., max_length=120)
    model_name: str = Field(..., max_length=200)
    vram_gb: int | None = Field(default=None, ge=0, le=4096)
    quantity: int = Field(default=1, ge=1, le=1000)
    condition_claimed: str = Field(default="Unknown", max_length=200)
    intended_outcome: str = Field(..., max_length=80)
    use_case: list[str] = Field(default_factory=list)
    evidence_supplied: EvidenceSuppliedIn = Field(default_factory=EvidenceSuppliedIn)
    operator_notes: str = Field(default="", max_length=4000)
    consent: ConsentIn = Field(default_factory=ConsentIn)


@router.post("/intake")
def computeclaw_intake(payload: ComputeIntakeIn) -> dict[str, Any]:
    """Public intake · creates immutable owner-attested compute record."""
    try:
        intake, snapshot, envelope = submit_intake(payload.model_dump())
    except IntakeValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {
        "asset_intake_id": intake.asset_intake_id,
        "readiness_snapshot": {
            "asset_intake_id": snapshot.asset_intake_id,
            "asset_summary": snapshot.asset_summary,
            "intended_outcome": snapshot.intended_outcome,
            "evidence_supplied_summary": snapshot.evidence_supplied_summary,
            "benchmark_status": snapshot.benchmark_status,
            "observed_market_eligible": snapshot.observed_market_eligible,
            "utility_evidence_status": snapshot.utility_evidence_status,
            "readiness_status": snapshot.readiness_status,
            "recommended_next_steps": snapshot.recommended_next_steps,
            "doctrine_disclaimer": snapshot.doctrine_disclaimer,
        },
        "bakery_envelope": envelope,
    }


@router.get("/categories")
def computeclaw_categories() -> dict[str, Any]:
    """Public · return the asset type + category catalogue."""
    return {
        "asset_types": list(ASSET_TYPES),
        "asset_categories": {
            category: list(models) for category, models in ASSET_CATEGORIES.items()
        },
        "supported_outcomes": list(SUPPORTED_OUTCOMES),
    }


@router.get("/readiness-statuses")
def computeclaw_readiness_statuses() -> dict[str, Any]:
    """Public · documents the AIOV readiness lifecycle."""
    return {
        "readiness_statuses": list(READINESS_STATUSES),
        "doctrine_note": (
            "AIOV draft moves through these states · INTAKE_ONLY is the "
            "default after intake · READY_FOR_VALIDATOR_REVIEW means the "
            "draft is complete enough to escalate to the Validator · "
            "no automated transition to DEED_ELIGIBILITY without manual review."
        ),
    }


# ─── Admin gate ──────────────────────────────────────────────────────


def _require_admin_token(x_ebay_admin_token: str | None) -> None:
    expected = get_settings().ebay_admin_token
    if not expected:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "EBAY_ADMIN_TOKEN is not configured on the server. "
                "Set it as a Fly secret to enable ComputeClaw admin routes."
            ),
        )
    if not x_ebay_admin_token or x_ebay_admin_token != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid or missing X-Ebay-Admin-Token header",
        )


# ─── Admin · MarketScout ─────────────────────────────────────────────


class MarketScoutSearchIn(BaseModel):
    query: str = Field(..., min_length=1, max_length=200)
    asset_category: str | None = Field(default=None, max_length=80)
    normalized_asset_name: str | None = Field(default=None, max_length=200)
    asset_intake_id: str | None = Field(default=None, max_length=80)
    limit: int = Field(default=10, ge=1, le=20)


@router.post("/admin/market-observations/ebay/search")
def admin_marketscout_search(
    payload: MarketScoutSearchIn,
    x_ebay_admin_token: str | None = Header(default=None),
):
    """Run a single eBay Browse observation batch · admin-gated.

    Requires COMPUTECLAW_MARKET_OBSERVATION_ENABLED=true on the server.
    Returns a safe summary · raw seller account details are NOT included.
    """
    _require_admin_token(x_ebay_admin_token)
    try:
        batch = collect_observations(
            query=payload.query,
            asset_category=payload.asset_category,
            normalized_asset_name=payload.normalized_asset_name,
            asset_intake_id=payload.asset_intake_id,
            limit=payload.limit,
        )
    except MarketScoutDisabled as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception as exc:  # noqa: BLE001
        _log.exception("MarketScout search failed")
        raise HTTPException(
            status_code=502,
            detail=f"MarketScout call failed · {type(exc).__name__}: {exc}",
        )
    return safe_summarize_batch(batch, max_items=5)


# ─── Admin · BenchInspector ──────────────────────────────────────────


class BenchmarkAttachIn(BaseModel):
    asset_intake_id: str = Field(..., min_length=1, max_length=80)
    benchmark_type: str = Field(default="DEFENDABLE_COMPUTE_INSPECTION", max_length=80)
    machine_identity_hash: str | None = Field(default=None, max_length=200)
    gpu_model_observed: str | None = Field(default=None, max_length=200)
    vram_observed_gb: int | None = Field(default=None, ge=0, le=4096)
    benchmark_run_id: str | None = Field(default=None, max_length=200)
    receipt_path: str | None = Field(default=None, max_length=500)
    verified: bool = Field(default=False)


@router.post("/admin/benchmark-evidence/attach")
def admin_attach_benchmark(
    payload: BenchmarkAttachIn,
    x_ebay_admin_token: str | None = Header(default=None),
):
    _require_admin_token(x_ebay_admin_token)
    try:
        evidence, envelope = attach_benchmark_evidence(
            asset_intake_id=payload.asset_intake_id,
            benchmark_type=payload.benchmark_type,
            machine_identity_hash=payload.machine_identity_hash,
            gpu_model_observed=payload.gpu_model_observed,
            vram_observed_gb=payload.vram_observed_gb,
            benchmark_run_id=payload.benchmark_run_id,
            receipt_path=payload.receipt_path,
            verified=payload.verified,
        )
    except BenchmarkAttachError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"benchmark_evidence": evidence.to_dict(), **envelope}


# ─── Admin · UtilitySignal ───────────────────────────────────────────


class UtilityAttachIn(BaseModel):
    asset_intake_id: str = Field(..., min_length=1, max_length=80)
    utility_source: str = Field(..., max_length=80)
    rental_hourly_rate: float | None = Field(default=None, ge=0)
    rental_duration_hours: float | None = Field(default=None, ge=0)
    gross_revenue_observed: float | None = Field(default=None, ge=0)
    receipt_path: str | None = Field(default=None, max_length=500)
    fleet_verified: bool = Field(default=False)


@router.post("/admin/utility-evidence/attach")
def admin_attach_utility(
    payload: UtilityAttachIn,
    x_ebay_admin_token: str | None = Header(default=None),
):
    _require_admin_token(x_ebay_admin_token)
    try:
        evidence, envelope = attach_utility_evidence(
            asset_intake_id=payload.asset_intake_id,
            utility_source=payload.utility_source,
            rental_hourly_rate=payload.rental_hourly_rate,
            rental_duration_hours=payload.rental_duration_hours,
            gross_revenue_observed=payload.gross_revenue_observed,
            receipt_path=payload.receipt_path,
            fleet_verified=payload.fleet_verified,
        )
    except UtilityAttachError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"utility_evidence": evidence.to_dict(), **envelope}


# ─── Admin · ValueComposer ───────────────────────────────────────────


class AIOVDraftComposeIn(BaseModel):
    intake: dict[str, Any] = Field(...)
    market_observation_summary: dict[str, Any] | None = Field(default=None)
    benchmark_evidence: dict[str, Any] | None = Field(default=None)
    utility_evidence: dict[str, Any] | None = Field(default=None)


@router.post("/admin/aiov-draft/compose")
def admin_compose_aiov_draft(
    payload: AIOVDraftComposeIn,
    x_ebay_admin_token: str | None = Header(default=None),
):
    _require_admin_token(x_ebay_admin_token)
    try:
        draft, envelope = compose_draft(
            intake=payload.intake,
            market_observation_summary=payload.market_observation_summary,
            benchmark_evidence=payload.benchmark_evidence,
            utility_evidence=payload.utility_evidence,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"aiov_draft": draft.to_dict(), **envelope}
