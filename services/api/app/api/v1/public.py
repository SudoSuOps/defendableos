"""Public verification endpoints · privacy-safe AND lifecycle-honest."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.deed import DefendableDeed
from app.services.deed import is_draft_deed, render_public_preview

router = APIRouter()


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
