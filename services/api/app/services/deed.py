"""Defendable Deed generation and privacy filtering."""
from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone

from slugify import slugify
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.ai import AIOVAnalysis
from app.models.asset import Asset
from app.models.deed import DeedStatus, DefendableDeed
from app.models.evidence import EvidenceManifest, ManifestStatus
from app.models.validator import ValidatorReview, ValidatorStatus
from app.services.hashing import sha256_json


class DeedPrerequisiteError(ValueError):
    """Raised when deed creation lacks required upstream artifacts."""


def _latest_manifest(db: Session, asset_id) -> EvidenceManifest | None:
    return (
        db.query(EvidenceManifest)
        .filter(
            EvidenceManifest.asset_id == asset_id,
            EvidenceManifest.status == ManifestStatus.CURRENT,
        )
        .order_by(EvidenceManifest.version.desc())
        .first()
    )


def _latest_aiov(db: Session, asset_id) -> AIOVAnalysis | None:
    return (
        db.query(AIOVAnalysis)
        .filter(AIOVAnalysis.asset_id == asset_id)
        .order_by(AIOVAnalysis.version.desc())
        .first()
    )


def _latest_validator(db: Session, asset_id) -> ValidatorReview | None:
    return (
        db.query(ValidatorReview)
        .filter(ValidatorReview.asset_id == asset_id)
        .order_by(ValidatorReview.version.desc())
        .first()
    )


DRAFT_DISCLAIMER = (
    "This is a draft evidence and analysis record prepared for review. "
    "No final valuation, professional appraisal, legal certification, "
    "authentication guarantee, issued Defendable Deed, public verification "
    "publication, or ENS issuance has occurred. Private evidence is "
    "referenced by hash only and is not displayed on this page."
)


def build_deed_payload(
    asset: Asset,
    manifest: EvidenceManifest,
    aiov: AIOVAnalysis | None,
    validator: ValidatorReview,
    deed_version: int,
    organization_ens_name: str | None,
    proposed_ens_name: str | None,
) -> dict:
    """Build the canonical draft-deed JSON payload.

    All new deeds start in DRAFT_REVIEW_RECORD state. Doctrine-correct fields:
      · created_at (not issued_at — there's no issuance yet)
      · validator_review.status = PASSED_FOR_DRAFT_PACKAGING
      · publication_policy block
      · explicit "_issued" booleans (all false at draft time)
    """
    profile = asset.compute_profile
    created_at = datetime.now(tz=timezone.utc).isoformat()
    return {
        "deed_type": "DEFENDABLE_DEED",
        "deed_version": f"0.{deed_version}",
        "record_status": "DRAFT_REVIEW_RECORD",
        "created_at": created_at,
        "issued_at": None,  # explicit · no issuance has happened
        "proof_of_value": {
            "framework": "DEFENDABLEOS",
            "doctrine": "VALIDATE_THE_VALIDATOR",
            "intelligence_engine": "AIOV",
            "record_purpose": "Evidence-backed asset value package prepared for review",
        },
        "asset": {
            "asset_reference": asset.public_asset_reference,
            "asset_class": asset.asset_class.value,
            "category": asset.category,
            "manufacturer": profile.manufacturer if profile else None,
            "model": profile.model if profile else None,
        },
        "evidence_packet": {
            "manifest_id": str(manifest.id),
            "manifest_sha256": manifest.manifest_sha256,
            "evidence_item_count": len(manifest.manifest_json.get("items", [])),
            "public_evidence_disclosure": "PRIVATE_EVIDENCE_REFERENCED_BY_HASH_ONLY",
        },
        "aiov_analysis": (
            {
                "analysis_id": str(aiov.id),
                "status": aiov.status.value,
                "value_display_status": (aiov.analysis_json or {})
                .get("value_opinion", {})
                .get("display_status", "WITHHELD_PENDING_VALIDATOR_REVIEW"),
                "valuation_issued": False,
            }
            if aiov
            else None
        ),
        "validator_review": {
            "protocol": "VALIDATE_THE_VALIDATOR",
            "receipt_id": str(validator.id),
            # Embedded in a DRAFT deed · doctrine status is DRAFT_PACKAGING.
            "status": "PASSED_FOR_DRAFT_PACKAGING",
            "receipt_sha256": validator.receipt_sha256,
            "human_approval_required": True,
        },
        "ens_identity": {
            "name": proposed_ens_name,
            "status": "RESERVED_NOT_ISSUED",
            "public_resolution_target": None,
            "parent_organization_ens": organization_ens_name,
        },
        "publication_policy": {
            "public_preview_allowed": True,
            "public_verification_status": "NOT_PUBLISHED",
            "ens_published": False,
            "value_claim_public": False,
            "publication_requires_human_approval": True,
        },
        "disclosures": {
            "ai_assisted_record": True,
            "professional_appraisal": False,
            "legal_certification": False,
            "authentication_guarantee": False,
            "final_valuation_issued": False,
            "deed_issued": False,
            "disclaimer": DRAFT_DISCLAIMER,
        },
    }


def create_deed(db: Session, asset: Asset, issued_by_user_id: uuid.UUID | None = None) -> DefendableDeed:
    manifest = _latest_manifest(db, asset.id)
    if manifest is None:
        raise DeedPrerequisiteError("No current evidence manifest. Upload evidence first.")
    aiov = _latest_aiov(db, asset.id)
    validator = _latest_validator(db, asset.id)
    if validator is None:
        raise DeedPrerequisiteError("No validator review. Run the validator first.")
    if validator.status == ValidatorStatus.FAILED_REQUIRES_REPAIR:
        raise DeedPrerequisiteError(
            "Validator review failed · cannot package a deed with blocking findings."
        )

    latest = (
        db.query(DefendableDeed)
        .filter(DefendableDeed.asset_id == asset.id)
        .order_by(DefendableDeed.version.desc())
        .first()
    )
    next_version = (latest.version + 1) if latest else 1
    if latest:
        latest.status = DeedStatus.SUPERSEDED
        db.flush()

    org = asset.organization
    org_ens = org.ens_name
    org_slug = org.ens_label or slugify(org.slug)
    asset_slug_part = re.sub(r"[^a-z0-9-]", "-", asset.public_asset_reference.lower()).strip("-")
    proposed_ens = f"ddeed-{asset_slug_part}.{org_slug}.{settings.ens_parent_name}"

    payload = build_deed_payload(
        asset=asset,
        manifest=manifest,
        aiov=aiov,
        validator=validator,
        deed_version=next_version,
        organization_ens_name=org_ens,
        proposed_ens_name=proposed_ens,
    )
    # Canonical hash · then nest under integrity block so the algorithm + canonical
    # form are named explicitly. The hash never gets re-computed on render.
    record_hash = sha256_json(payload)
    payload["integrity"] = {
        "hash_algorithm": "SHA-256",
        "canonicalization": "DEFENDABLE_CANONICAL_JSON_V1",
        "record_hash": record_hash,
    }

    deed = DefendableDeed(
        id=uuid.uuid4(),
        organization_id=asset.organization_id,
        asset_id=asset.id,
        deed_reference=f"DDEED-{asset.public_asset_reference}-v{next_version}",
        version=next_version,
        status=DeedStatus.DRAFT_REVIEW_RECORD,
        deed_json=payload,
        record_hash=record_hash,
        public_slug=None,
        is_public=False,
        issued_by=issued_by_user_id,
    )
    db.add(deed)
    db.flush()
    return deed


# ── Privacy filter for public verification ──────────────────────────────────
def filter_public_payload(deed_json: dict) -> dict:
    """Return a deep-copied payload safe for public exposure.

    Strips potentially-sensitive fields that the original payload should never
    contain at this point, but the filter is the belt-and-braces guard.
    """
    import copy

    public = copy.deepcopy(deed_json)
    # Asset section: drop anything that could leak private serial / cost data.
    asset = public.get("asset", {})
    asset.pop("serial_number", None)
    asset.pop("private_serial_number", None)
    asset.pop("purchase_cost", None)
    asset.pop("purchase_cost_private", None)
    public["asset"] = asset
    # AIOV analysis: drop narrative if present.
    aiov = public.get("aiov_analysis")
    if aiov:
        aiov.pop("narrative", None)
        aiov.pop("private_notes", None)
    # Evidence packet: only manifest hash + count, never individual filenames.
    ep = public.get("evidence_packet", {})
    for key in list(ep.keys()):
        if key not in {"manifest_sha256", "evidence_item_count", "public_evidence_disclosure", "manifest_id"}:
            ep.pop(key)
    public["evidence_packet"] = ep
    return public


def is_draft_deed(deed: DefendableDeed) -> bool:
    """Conservative draft detection · ANY of the spec's four conditions → draft.

    A deed is treated as DRAFT until it has cleared every issuance prerequisite.
    There is currently NO code path that flips a deed out of draft state; future
    issuance work will add one with human approval + ENS write + value disclosure.
    """
    raw = deed.deed_json or {}
    if raw.get("record_status") == "DRAFT_REVIEW_RECORD":
        return True
    if not raw.get("issued_at"):
        return True
    ens_status = (raw.get("ens_identity") or {}).get("status")
    if ens_status in {"RESERVED_NOT_ISSUED", None, "REVOKED"}:
        return True
    value_status = (raw.get("aiov_analysis") or {}).get("value_display_status")
    if value_status == "WITHHELD_PENDING_VALIDATOR_REVIEW":
        return True
    return False


def render_public_preview(deed: DefendableDeed) -> dict:
    """Compose the doctrine-correct public preview payload for a deed.

    This is the single source of truth for what /verify/{slug} and
    /verify/{slug}.json return. Works on BOTH new schema (created_at + integrity
    block + publication_policy) and OLD schema (issued_at + bare record_hash)
    by always recomputing the draft-aware structure from the deed row + json.

    For a DRAFT deed:
      · issued_at = null
      · created_at = deed.created_at
      · record_status forced back to DRAFT_REVIEW_RECORD (even if stored as
        APPROVED_FOR_PUBLIC by the legacy publish flow — preview-publish is
        not record issuance)
      · validator_review.status = PASSED_FOR_DRAFT_PACKAGING
      · publication_policy emits NOT_PUBLISHED
      · all "_issued" booleans = false
    """
    import copy

    raw = copy.deepcopy(deed.deed_json or {})
    public = filter_public_payload(raw)
    is_draft = is_draft_deed(deed)
    record_status = "DRAFT_REVIEW_RECORD" if is_draft else (
        public.get("record_status") or "DRAFT_REVIEW_RECORD"
    )

    # ── timestamp correction ────────────────────────────────────────────────
    if is_draft:
        public["issued_at"] = None
        # Prefer existing created_at on payload; otherwise use the DB row.
        public["created_at"] = public.get("created_at") or deed.created_at.isoformat()
    else:
        # Real issued record · keep both for clarity.
        public.setdefault("created_at", deed.created_at.isoformat())

    # ── validator status correction ─────────────────────────────────────────
    vr = public.get("validator_review")
    if isinstance(vr, dict):
        if is_draft and vr.get("status") == "PASSED_FOR_PACKAGING":
            vr["status"] = "PASSED_FOR_DRAFT_PACKAGING"
        vr.setdefault("human_approval_required", True)
        public["validator_review"] = vr

    # ── aiov · explicit valuation flag ──────────────────────────────────────
    aiov = public.get("aiov_analysis")
    if isinstance(aiov, dict):
        aiov.setdefault("valuation_issued", False)
        public["aiov_analysis"] = aiov

    # ── publication_policy · always emit (derive from current state) ───────
    public["publication_policy"] = {
        "public_preview_allowed": True,
        "public_verification_status": "NOT_PUBLISHED" if is_draft else "PUBLISHED",
        "ens_published": (public.get("ens_identity") or {}).get("status") not in {
            None, "RESERVED_NOT_ISSUED", "REVOKED",
        },
        "value_claim_public": (
            not is_draft
            and (public.get("aiov_analysis") or {}).get("value_display_status")
            == "REVIEWED_AND_DISCLOSED"
        ),
        "publication_requires_human_approval": True,
    }

    # ── disclosures · explicit "_issued" booleans ───────────────────────────
    disclosures = public.get("disclosures") or {}
    disclosures.setdefault("ai_assisted_record", True)
    disclosures.setdefault("professional_appraisal", False)
    disclosures.setdefault("legal_certification", False)
    disclosures.setdefault("authentication_guarantee", False)
    disclosures["final_valuation_issued"] = not is_draft and disclosures.get(
        "final_valuation_issued", False
    )
    disclosures["deed_issued"] = not is_draft and disclosures.get("deed_issued", False)
    # ALWAYS use the draft disclaimer text for drafts · doctrine canonical.
    if is_draft:
        disclosures["disclaimer"] = DRAFT_DISCLAIMER
    public["disclosures"] = disclosures

    # ── integrity block · move record_hash here if not already ─────────────
    if "integrity" not in public:
        existing_hash = public.pop("record_hash", None) or deed.record_hash
        public["integrity"] = {
            "hash_algorithm": "SHA-256",
            "canonicalization": "DEFENDABLE_CANONICAL_JSON_V1",
            "record_hash": existing_hash,
        }
    else:
        # New-schema payload · drop any duplicate top-level record_hash.
        public.pop("record_hash", None)

    public["record_status"] = record_status
    return public


def hard_block_real_publication(deed: DefendableDeed) -> tuple[bool, list[str]]:
    """Doctrine gate: a deed CANNOT be marked as issued/published-as-record while
    any of these draft conditions remain. Returns (blocked, reasons).

    Note: this does NOT block public PREVIEW publication (today's `publish_public`).
    It blocks any future code path that would claim issued/ENS-anchored semantics.
    """
    reasons: list[str] = []
    raw = deed.deed_json or {}
    if deed.status == DeedStatus.DRAFT_REVIEW_RECORD:
        reasons.append("record_status is DRAFT_REVIEW_RECORD")
    if not raw.get("issued_at"):
        reasons.append("issued_at is null")
    ens_status = (raw.get("ens_identity") or {}).get("status")
    if ens_status == "RESERVED_NOT_ISSUED":
        reasons.append("ENS status is RESERVED_NOT_ISSUED")
    value_status = (raw.get("aiov_analysis") or {}).get("value_display_status")
    if value_status == "WITHHELD_PENDING_VALIDATOR_REVIEW":
        reasons.append("value_display_status is WITHHELD_PENDING_VALIDATOR_REVIEW")
    return (len(reasons) > 0, reasons)


def publish_public(deed: DefendableDeed) -> str:
    """Assign a stable slug for the PUBLIC PREVIEW page.

    This is NOT a record issuance · the deed remains DRAFT_REVIEW_RECORD until
    human approval + ENS issuance occur via a separate workflow. The slug
    enables `/verify/{slug}` to render the draft preview (with all the
    NOT_PUBLISHED, RESERVED_NOT_ISSUED status markers visible).
    """
    if deed.public_slug is None:
        slug_base = re.sub(r"[^a-z0-9-]", "-", deed.deed_reference.lower()).strip("-")
        deed.public_slug = slug_base[:96]
    deed.is_public = True
    # NOTE: deed.status stays DRAFT_REVIEW_RECORD · the deed itself is not yet
    # an issued record. Only the PREVIEW is now publicly viewable. Setting
    # APPROVED_FOR_PUBLIC would have implied issuance; we hold the line.
    return deed.public_slug
