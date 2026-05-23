"""Claw Bakery SHA-256 receipt service.

A receipt binds:
  · artifact_type (intake | snapshot | pair_candidate | dataset_release | ...)
  · artifact_key (storage key)
  · sha256 (deterministic over the stored bytes)
  · source_run_id
  · tribunal_label / redaction_status / consent_status (snapshot at receipt time)
  · created_at

Receipts are themselves stored as immutable JSON artifacts under
claw-bakery/receipts/sha256/. A manifest bundles N receipts into one
artifact under claw-bakery/receipts/manifests/.
"""
from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Any, Literal

from app.services.claw_bakery.bakery_storage import BakeryStore, get_bakery_store


ArtifactType = Literal[
    "intake", "snapshot", "pair_candidate", "redacted_record",
    "dataset_release", "benchmark_pack", "validator_review",
]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def generate_receipt(
    *,
    artifact_type: ArtifactType,
    artifact_key: str,
    artifact_bytes: bytes,
    source_run_id: str,
    tribunal_label: str = "PENDING",
    redaction_status: str = "PENDING",
    consent_status: dict[str, Any] | None = None,
    extra_metadata: dict[str, Any] | None = None,
    store: BakeryStore | None = None,
) -> dict[str, Any]:
    """Produce a SHA-256 receipt for an already-stored artifact.

    `artifact_bytes` MUST be the exact bytes that were written to storage
    · the receipt's sha256 is the digest of those bytes, not of any
    higher-level representation.
    """
    store = store or get_bakery_store()
    sha256 = hashlib.sha256(artifact_bytes).hexdigest()
    receipt_id = f"DCLAW-RECEIPT-{uuid.uuid4().hex[:12].upper()}"
    receipt = {
        "receipt_id": receipt_id,
        "artifact_type": artifact_type,
        "artifact_key": artifact_key,
        "byte_size": len(artifact_bytes),
        "sha256": sha256,
        "source_run_id": source_run_id,
        "tribunal_label": tribunal_label,
        "redaction_status": redaction_status,
        "consent_status": consent_status or {},
        "extra_metadata": extra_metadata or {},
        "created_at": _now(),
    }
    artifact = store.put_receipt(receipt_id, receipt)
    receipt["receipt_artifact_key"] = artifact.key
    receipt["receipt_self_sha256"] = artifact.sha256
    return receipt


def build_manifest(
    *,
    manifest_id: str,
    title: str,
    receipt_ids: list[str],
    receipts: list[dict[str, Any]],
    store: BakeryStore | None = None,
) -> dict[str, Any]:
    """Bundle a list of receipts into a manifest artifact."""
    store = store or get_bakery_store()
    # Manifest sha256 covers the canonical JSON of sorted receipt_ids + their sha256s,
    # so any drift in any receipt is detectable from the manifest alone.
    manifest_content_for_hash = json.dumps(
        sorted(
            ({"receipt_id": r["receipt_id"], "sha256": r["sha256"]} for r in receipts),
            key=lambda r: r["receipt_id"],
        ),
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    manifest_sha256 = hashlib.sha256(manifest_content_for_hash).hexdigest()
    payload = {
        "manifest_id": manifest_id,
        "title": title,
        "receipt_count": len(receipts),
        "receipt_ids": sorted(receipt_ids),
        "receipts": receipts,
        "manifest_sha256": manifest_sha256,
        "created_at": _now(),
    }
    artifact = store.put_manifest(manifest_id, payload)
    payload["manifest_artifact_key"] = artifact.key
    return payload
