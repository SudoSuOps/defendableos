"""ArtifactRegistry-aware object storage service.

Wraps the existing boto3-based ObjectStore with:
  · 4-bucket privacy-boundary routing (PRIVATE_EVIDENCE,
    MARKET_OBSERVATIONS, DERIVED_DATASETS, PUBLIC_ASSETS) per the
    Goods Vault architecture
  · ArtifactRegistry persistence on every put · the registry is the
    single source of truth for "what objects exist, where they live,
    and under what rights status"
  · SHA-256 hashing + manifest read/write helpers
  · Hard refusal to expose PRIVATE_EVIDENCE objects via the public
    export helper · doctrine boundary enforced at the service layer

This module is provider-agnostic · MinIOObjectStore and
TigrisObjectStore look identical at the wire level (both are
S3-sigv4 endpoints) so we use the same boto3 client and switch via
config.object_storage_provider.
"""
from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.goods import (
    ArtifactPrivacyClass,
    ArtifactRegistry,
    ArtifactType,
    RightsStatus,
)


@dataclass
class StoredArtifact:
    """In-memory result of a write · matches ArtifactRegistry shape."""
    id: uuid.UUID
    bucket: str
    object_key: str
    sha256: str
    byte_size: int
    artifact_type: ArtifactType
    privacy_class: ArtifactPrivacyClass


def sha256_bytes(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def _bucket_for_privacy_class(privacy_class: ArtifactPrivacyClass) -> str:
    """Resolve the bucket name for a given privacy boundary.

    PRIVATE_EVIDENCE   → private-evidence bucket (client uploads, deed evidence)
    MARKET_OBSERVATIONS → private platform-research bucket (Brave/eBay)
    DERIVED_DATASETS    → private dataset/pair-factory bucket
    PUBLIC_ASSETS       → privacy-filtered public exports only
    """
    if privacy_class == ArtifactPrivacyClass.PRIVATE_EVIDENCE:
        return settings.s3_private_evidence_bucket
    if privacy_class == ArtifactPrivacyClass.MARKET_OBSERVATIONS:
        return settings.s3_market_observations_bucket
    if privacy_class == ArtifactPrivacyClass.DERIVED_DATASETS:
        return settings.s3_derived_datasets_bucket
    if privacy_class == ArtifactPrivacyClass.PUBLIC_ASSETS:
        return settings.s3_public_assets_bucket
    raise ValueError(f"Unknown privacy class: {privacy_class!r}")


def _client() -> Any:
    """boto3 S3 client · same wire protocol for MinIO/Tigris/S3."""
    return boto3.client(
        "s3",
        endpoint_url=settings.s3_endpoint_url,
        aws_access_key_id=settings.s3_access_key_id,
        aws_secret_access_key=settings.s3_secret_access_key,
        region_name=settings.s3_region,
        config=Config(signature_version="s3v4"),
    )


def put_artifact(
    db: Session,
    *,
    body: bytes,
    object_key: str,
    artifact_type: ArtifactType,
    privacy_class: ArtifactPrivacyClass,
    mime_type: str | None = None,
    rights_status: RightsStatus = RightsStatus.INTERNAL_RESEARCH_ONLY,
    owner_organization_id: uuid.UUID | None = None,
    asset_id: uuid.UUID | None = None,
    goods_id: uuid.UUID | None = None,
    discovery_run_id: uuid.UUID | None = None,
    pair_batch_id: uuid.UUID | None = None,
    retention_policy: str | None = None,
) -> StoredArtifact:
    """Write a single artifact + register it in ArtifactRegistry.

    No bytes leave the platform unless OBJECT_STORAGE_LIVE_ENABLED is set ·
    when disabled we still compute the hash + register the entry but skip
    the S3 PUT (test/local-only mode). Production calls flip the flag.
    """
    digest = sha256_bytes(body)
    bucket = _bucket_for_privacy_class(privacy_class)

    if settings.object_storage_live_enabled:
        c = _client()
        kwargs: dict = {"Bucket": bucket, "Key": object_key, "Body": body}
        if mime_type:
            kwargs["ContentType"] = mime_type
        c.put_object(**kwargs)

    registry_row = ArtifactRegistry(
        id=uuid.uuid4(),
        bucket=bucket,
        object_key=object_key,
        artifact_type=artifact_type,
        privacy_class=privacy_class,
        owner_organization_id=owner_organization_id,
        asset_id=asset_id,
        goods_id=goods_id,
        discovery_run_id=discovery_run_id,
        pair_batch_id=pair_batch_id,
        sha256=digest,
        mime_type=mime_type,
        byte_size=len(body),
        rights_status=rights_status,
        retention_policy=retention_policy,
    )
    db.add(registry_row)
    db.flush()
    return StoredArtifact(
        id=registry_row.id,
        bucket=bucket,
        object_key=object_key,
        sha256=digest,
        byte_size=len(body),
        artifact_type=artifact_type,
        privacy_class=privacy_class,
    )


def get_artifact_bytes(artifact: ArtifactRegistry) -> bytes:
    """Read bytes back from object storage (live mode only)."""
    if not settings.object_storage_live_enabled:
        raise RuntimeError(
            "OBJECT_STORAGE_LIVE_ENABLED is false · cannot fetch artifact body. "
            "Set the env var to enable real S3 reads."
        )
    c = _client()
    resp = c.get_object(Bucket=artifact.bucket, Key=artifact.object_key)
    return resp["Body"].read()


def public_export_or_refuse(artifact: ArtifactRegistry) -> bytes:
    """Doctrine guard · refuses to return bytes when the artifact is private.

    The ONLY artifact that may be served via public export paths is one
    whose `privacy_class == PUBLIC_ASSETS`. Anything else raises ·
    callers like the /verify route must use this helper, never the raw
    `get_artifact_bytes()`.
    """
    if artifact.privacy_class != ArtifactPrivacyClass.PUBLIC_ASSETS:
        raise PermissionError(
            f"Artifact {artifact.id} has privacy_class={artifact.privacy_class.value} · "
            "public export blocked by doctrine."
        )
    return get_artifact_bytes(artifact)


def write_manifest(
    db: Session,
    *,
    manifest_payload: dict,
    object_key: str,
    artifact_type: ArtifactType,
    privacy_class: ArtifactPrivacyClass,
    **kwargs: Any,
) -> StoredArtifact:
    """Write a JSON manifest deterministically · sort_keys + UTF-8."""
    body = json.dumps(manifest_payload, sort_keys=True, indent=2).encode("utf-8")
    return put_artifact(
        db,
        body=body,
        object_key=object_key,
        artifact_type=artifact_type,
        privacy_class=privacy_class,
        mime_type="application/json",
        **kwargs,
    )


def verify_sha256(artifact: ArtifactRegistry, body: bytes) -> bool:
    """Recompute SHA-256 on supplied body + compare to registry record."""
    return sha256_bytes(body) == artifact.sha256


def generate_presigned_upload(
    bucket: str,
    object_key: str,
    expires_seconds: int | None = None,
    content_type: str | None = None,
) -> dict:
    """Generate a presigned PUT URL · honors S3_PRESIGNED_URL_TTL_SECONDS."""
    if not settings.object_storage_live_enabled:
        raise RuntimeError("object_storage_live_enabled must be true for presigned URLs")
    c = _client()
    ttl = expires_seconds or settings.s3_presigned_url_ttl_seconds
    params: dict = {"Bucket": bucket, "Key": object_key}
    if content_type:
        params["ContentType"] = content_type
    url = c.generate_presigned_url("put_object", Params=params, ExpiresIn=ttl)
    return {"url": url, "expires_in": ttl, "bucket": bucket, "object_key": object_key}


def object_exists(bucket: str, object_key: str) -> bool:
    if not settings.object_storage_live_enabled:
        return False
    c = _client()
    try:
        c.head_object(Bucket=bucket, Key=object_key)
        return True
    except ClientError as e:
        if e.response["Error"]["Code"] in {"404", "NoSuchKey", "NotFound"}:
            return False
        raise


def safe_object_key(*parts: str) -> str:
    """Compose a safe object key from path components."""
    cleaned = [p.strip("/").replace("..", "_") for p in parts if p]
    return "/".join(cleaned)


def ts_partition() -> tuple[str, str, str]:
    """YYYY / MM / DD partition components for time-bucketed paths."""
    now = datetime.now(timezone.utc)
    return f"{now.year:04d}", f"{now.month:02d}", f"{now.day:02d}"
