"""Public verification endpoints · privacy-safe by construction."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.deed import DefendableDeed
from app.services.deed import filter_public_payload

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


@router.get("/public/verify/{public_record_slug}")
def public_record(public_record_slug: str, db: Session = Depends(get_db)) -> dict:
    deed = _load_public_deed(db, public_record_slug)
    payload = filter_public_payload(deed.deed_json)
    return {
        "public_slug": deed.public_slug,
        "deed_reference": deed.deed_reference,
        "version": deed.version,
        "record_hash": deed.record_hash,
        "issued_at": deed.deed_json.get("issued_at"),
        "deed_public": payload,
    }


@router.get("/public/verify/{public_record_slug}.json")
def public_record_json(public_record_slug: str, db: Session = Depends(get_db)) -> JSONResponse:
    deed = _load_public_deed(db, public_record_slug)
    payload = filter_public_payload(deed.deed_json)
    return JSONResponse(payload)
