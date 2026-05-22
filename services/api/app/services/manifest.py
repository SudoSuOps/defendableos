"""Evidence manifest generation · the receipt that travels with the asset."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.asset import Asset
from app.models.evidence import (
    EvidenceItem,
    EvidenceManifest,
    ManifestStatus,
)
from app.services.hashing import sha256_json
from app.services.storage import get_object_store, manifest_key


def build_manifest_payload(asset: Asset, items: list[EvidenceItem]) -> dict:
    return {
        "manifest_type": "DEFENDABLE_EVIDENCE_MANIFEST",
        "version": 1,
        "asset_reference": asset.public_asset_reference,
        "asset_id": str(asset.id),
        "organization_id": str(asset.organization_id),
        "generated_at": datetime.now(tz=timezone.utc).isoformat(),
        "items": [
            {
                "evidence_item_id": str(it.id),
                "evidence_type": it.evidence_type.value,
                "filename": it.filename,
                "content_type": it.content_type,
                "byte_size": it.byte_size,
                "sha256": it.sha256_hash,
                "visibility": it.visibility.value,
                "ingestion_status": it.ingestion_status.value,
                "provenance": it.provenance,
            }
            for it in items
        ],
    }


def regenerate_manifest(db: Session, asset: Asset) -> EvidenceManifest:
    """Mark all current manifests for this asset superseded, then create a new one."""
    db.query(EvidenceManifest).filter(
        EvidenceManifest.asset_id == asset.id,
        EvidenceManifest.status == ManifestStatus.CURRENT,
    ).update({"status": ManifestStatus.SUPERSEDED})

    items = list(
        db.scalars(
            select(EvidenceItem).where(EvidenceItem.asset_id == asset.id).order_by(EvidenceItem.created_at)
        )
    )

    latest_version = (
        db.query(EvidenceManifest)
        .filter(EvidenceManifest.asset_id == asset.id)
        .order_by(EvidenceManifest.version.desc())
        .first()
    )
    next_version = (latest_version.version + 1) if latest_version else 1

    payload = build_manifest_payload(asset, items)
    payload["version"] = next_version
    manifest_hash = sha256_json(payload)
    payload["manifest_sha256"] = manifest_hash

    manifest = EvidenceManifest(
        id=uuid.uuid4(),
        asset_id=asset.id,
        version=next_version,
        manifest_json=payload,
        manifest_sha256=manifest_hash,
        status=ManifestStatus.CURRENT,
    )
    db.add(manifest)
    db.flush()

    # Mirror manifest into private object storage (best-effort).
    try:
        store = get_object_store()
        key = manifest_key(asset.organization_id, asset.id, next_version)
        store.put_private(
            key=key,
            body=__import__("json").dumps(payload, indent=2, sort_keys=True).encode("utf-8"),
            content_type="application/json",
        )
    except Exception:
        pass

    return manifest


def get_current_manifest(db: Session, asset_id) -> EvidenceManifest | None:
    return (
        db.query(EvidenceManifest)
        .filter(
            EvidenceManifest.asset_id == asset_id,
            EvidenceManifest.status == ManifestStatus.CURRENT,
        )
        .order_by(EvidenceManifest.version.desc())
        .first()
    )
