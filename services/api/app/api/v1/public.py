"""Public verification + ledger lookup endpoints · privacy-safe + lifecycle-honest."""
from __future__ import annotations

import re

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.deed import DefendableDeed
from app.models.evidence import EvidenceManifest
from app.models.validator import ValidatorReview
from app.services.deed import is_draft_deed, render_public_preview

router = APIRouter()

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_DEED_REF_RE = re.compile(r"^DDEED-[A-Z0-9-]+-v\d+$", re.IGNORECASE)


def _load_public_deed(db: Session, slug: str) -> DefendableDeed:
    deed = (
        db.query(DefendableDeed)
        .filter(DefendableDeed.public_slug == slug, DefendableDeed.is_public == True)  # noqa: E712
        .first()
    )
    if deed is None:
        raise HTTPException(status_code=404, detail="public record not found")
    return deed


def _decompose(deed: DefendableDeed, public: dict) -> dict:
    """Five-status decomposition surfaced at the top level of the response.

    Lets the UI render each status as its own chip without parsing the JSON.
    Uses the canonical is_draft_deed() detector (any of four blocker conditions
    → draft).
    """
    is_draft = is_draft_deed(deed)
    return {
        "record_status": "DRAFT_REVIEW_RECORD" if is_draft else deed.status.value,
        "validator_status": (public.get("validator_review") or {}).get("status")
        or ("PASSED_FOR_DRAFT_PACKAGING" if is_draft else "PASSED_FOR_PACKAGING"),
        "publication_status": "NOT_PUBLISHED" if is_draft else "PUBLISHED",
        "value_status": (public.get("aiov_analysis") or {}).get("value_display_status")
        or "WITHHELD_PENDING_VALIDATOR_REVIEW",
        "ens_status": (public.get("ens_identity") or {}).get("status")
        or "RESERVED_NOT_ISSUED",
        "is_draft": is_draft,
    }


# Register the `.json` route FIRST so it wins over the catch-all slug route.
@router.get("/public/verify/{public_record_slug}.json")
def public_record_json(public_record_slug: str, db: Session = Depends(get_db)) -> JSONResponse:
    deed = _load_public_deed(db, public_record_slug)
    payload = render_public_preview(deed)
    return JSONResponse(payload)


@router.get("/public/verify/{public_record_slug}")
def public_record(public_record_slug: str, db: Session = Depends(get_db)) -> dict:
    deed = _load_public_deed(db, public_record_slug)
    payload = render_public_preview(deed)
    lifecycle = _decompose(deed, payload)
    return {
        "public_slug": deed.public_slug,
        "deed_reference": deed.deed_reference,
        "version": deed.version,
        # honest timestamps · created_at always, issued_at only for issued records
        "created_at": deed.created_at.isoformat(),
        "issued_at": payload.get("issued_at"),
        "lifecycle": lifecycle,
        "deed_public": payload,
    }


# ─────────────────────────────────────────────────────────────────────────
# Ledger lookup · paste any Defendable hash, get the record it represents.
#
# Doctrine constraints:
#   · Only matches deeds where deed.is_public = True (preview-published)
#   · Never returns private evidence references · only resolves to a deed
#     and the canonical /verify URL
#   · Lifecycle decomposition is included so DRAFT records render with
#     draft-correct status chips client-side
#   · Supports four lookup kinds:
#       RECORD_HASH        deeds.record_hash
#       MANIFEST_HASH      evidence_manifests.manifest_sha256
#       VALIDATOR_RECEIPT  validator_reviews.receipt_sha256
#       DEED_REFERENCE     deeds.deed_reference (e.g. DDEED-DOV-COMPUTE-000001-v2)
# ─────────────────────────────────────────────────────────────────────────


def _build_lookup_response(
    kind: str,
    matched_hash: str,
    deed: DefendableDeed,
    **extra: object,
) -> dict:
    payload = render_public_preview(deed)
    lifecycle = _decompose(deed, payload)
    asset = payload.get("asset") or {}
    summary_parts = [asset.get("manufacturer") or "", asset.get("model") or ""]
    summary = " ".join(p for p in summary_parts if p).strip() or asset.get(
        "asset_reference", ""
    )
    return {
        "kind": kind,
        "matched_hash": matched_hash,
        "deed_reference": deed.deed_reference,
        "public_slug": deed.public_slug,
        "version": deed.version,
        "summary": summary,
        "asset_class": asset.get("asset_class"),
        "asset_reference": asset.get("asset_reference"),
        "verify_url": f"/verify/{deed.public_slug}",
        "showcase_url": f"/showcase/{deed.public_slug}",
        "lifecycle": lifecycle,
        "integrity": payload.get("integrity"),
        **extra,
    }


def _not_found(hash_input: str, detail: str | None = None) -> dict:
    return {
        "kind": "NOT_FOUND",
        "matched_hash": hash_input,
        "summary": detail
        or "No public Defendable record matches this hash. Records that are "
        "not yet preview-published are intentionally not discoverable here.",
        "lifecycle": None,
    }


@router.get("/public/lookup")
def public_lookup(
    hash: str = Query(
        ...,
        min_length=1,
        max_length=128,
        description=(
            "A SHA-256 (64 hex chars) or a deed reference like "
            "DDEED-DOV-COMPUTE-000001-v2"
        ),
    ),
    db: Session = Depends(get_db),
) -> dict:
    raw = (hash or "").strip()
    if not raw:
        return _not_found(raw, "Empty query.")

    # Deed reference form takes priority · case-insensitive SQL match because
    # we store the version suffix lowercase ("…-v2") and users will paste from
    # PDFs / emails / chat without preserving case.
    if _DEED_REF_RE.match(raw):
        deed = (
            db.query(DefendableDeed)
            .filter(func.upper(DefendableDeed.deed_reference) == raw.upper())
            .filter(DefendableDeed.is_public == True)  # noqa: E712
            .first()
        )
        if deed:
            return _build_lookup_response("DEED_REFERENCE", deed.deed_reference, deed)
        return _not_found(raw, "Deed reference is not preview-published.")

    h = raw.lower()
    if not _SHA256_RE.match(h):
        return _not_found(
            raw,
            "Input must be a SHA-256 hex string (64 chars) or a deed reference "
            "like DDEED-DOV-COMPUTE-000001-v2.",
        )

    # 1 · record_hash on a public deed
    deed = (
        db.query(DefendableDeed)
        .filter(DefendableDeed.record_hash == h)
        .filter(DefendableDeed.is_public == True)  # noqa: E712
        .first()
    )
    if deed:
        return _build_lookup_response("RECORD_HASH", h, deed)

    # 2 · manifest_sha256 · resolve to a public deed referencing that asset
    manifest = (
        db.query(EvidenceManifest)
        .filter(EvidenceManifest.manifest_sha256 == h)
        .first()
    )
    if manifest:
        deed = (
            db.query(DefendableDeed)
            .filter(DefendableDeed.asset_id == manifest.asset_id)
            .filter(DefendableDeed.is_public == True)  # noqa: E712
            .order_by(DefendableDeed.version.desc())
            .first()
        )
        if deed:
            return _build_lookup_response(
                "MANIFEST_HASH",
                h,
                deed,
                manifest_id=str(manifest.id),
                manifest_version=manifest.version,
            )

    # 3 · validator receipt_sha256 · resolve via the asset → public deed
    review = (
        db.query(ValidatorReview)
        .filter(ValidatorReview.receipt_sha256 == h)
        .first()
    )
    if review:
        deed = (
            db.query(DefendableDeed)
            .filter(DefendableDeed.asset_id == review.asset_id)
            .filter(DefendableDeed.is_public == True)  # noqa: E712
            .order_by(DefendableDeed.version.desc())
            .first()
        )
        if deed:
            return _build_lookup_response(
                "VALIDATOR_RECEIPT",
                h,
                deed,
                receipt_id=str(review.id),
                validator_version=review.version,
            )

    return _not_found(raw)
