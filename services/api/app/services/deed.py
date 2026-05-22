"""Defendable Deed generation and privacy filtering."""
from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone

from slugify import slugify
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.ai import AIOVAnalysis, AIOVStatus
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


def build_deed_payload(
    asset: Asset,
    manifest: EvidenceManifest,
    aiov: AIOVAnalysis | None,
    validator: ValidatorReview,
    deed_version: int,
    organization_ens_name: str | None,
    proposed_ens_name: str | None,
) -> dict:
    profile = asset.compute_profile
    return {
        "deed_type": "DEFENDABLE_DEED",
        "deed_version": f"0.{deed_version}",
        "record_status": "DRAFT_REVIEW_RECORD",
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
                .get("display_status", "WITHHELD_OR_REVIEWED_ONLY"),
            }
            if aiov
            else None
        ),
        "validator_review": {
            "protocol": "VALIDATE_THE_VALIDATOR",
            "receipt_id": str(validator.id),
            "status": validator.status.value,
            "receipt_sha256": validator.receipt_sha256,
        },
        "ens_identity": {
            "name": proposed_ens_name,
            "status": "RESERVED_NOT_ISSUED",
            "public_resolution_target": None,
            "parent_organization_ens": organization_ens_name,
        },
        "disclosures": {
            "ai_assisted_record": True,
            "professional_appraisal": False,
            "legal_certification": False,
            "authentication_guarantee": False,
            "disclaimer": (
                "This record is an evidence and analysis package. Asset-specific "
                "professional, legal, regulatory, licensing, authentication, "
                "insurance, or appraisal requirements may still apply."
            ),
        },
        "issued_at": datetime.now(tz=timezone.utc).isoformat(),
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
    record_hash = sha256_json(payload)
    payload["record_hash"] = record_hash

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
    # AIOV analysis: drop narrative if present (analysis_id + display_status only).
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


def publish_public(deed: DefendableDeed) -> str:
    """Assign a stable slug and flip the deed to APPROVED_FOR_PUBLIC."""
    if deed.public_slug is None:
        slug_base = re.sub(r"[^a-z0-9-]", "-", deed.deed_reference.lower()).strip("-")
        deed.public_slug = slug_base[:96]
    deed.is_public = True
    deed.status = DeedStatus.APPROVED_FOR_PUBLIC
    return deed.public_slug
