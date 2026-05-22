"""S3-compatible object storage wrapper (MinIO local · R2/S3 future).

All evidence is private by default. Public publication goes through a separate
deliberate workflow and only touches the public bucket.
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass

import boto3
from botocore.client import Config

from app.core.config import settings

_SAFE_KEY = re.compile(r"[^A-Za-z0-9._/\-]")


def safe_storage_key(*parts: str) -> str:
    """Build a defensively-sanitised storage key from path components.

    Rejects obvious traversal attempts and replaces unsafe characters. The result
    is suitable for use as an S3 object key.
    """
    cleaned: list[str] = []
    for p in parts:
        if not p:
            continue
        if ".." in p or p.startswith("/") or p.startswith("\\"):
            raise ValueError(f"unsafe path component: {p!r}")
        cleaned.append(_SAFE_KEY.sub("_", p))
    return "/".join(cleaned)


@dataclass
class StoredObject:
    bucket: str
    key: str
    byte_size: int
    sha256: str
    content_type: str | None


class ObjectStore:
    def __init__(self) -> None:
        self._client = boto3.client(
            "s3",
            endpoint_url=settings.s3_endpoint_url,
            aws_access_key_id=settings.s3_access_key_id,
            aws_secret_access_key=settings.s3_secret_access_key,
            region_name=settings.s3_region,
            config=Config(signature_version="s3v4"),
        )

    @property
    def private_bucket(self) -> str:
        return settings.s3_private_bucket

    @property
    def public_bucket(self) -> str:
        return settings.s3_public_bucket

    def ensure_buckets(self) -> None:
        for bucket in (self.private_bucket, self.public_bucket):
            try:
                self._client.head_bucket(Bucket=bucket)
            except Exception:
                try:
                    self._client.create_bucket(Bucket=bucket)
                except Exception:
                    pass

    def put_private(self, key: str, body: bytes, content_type: str | None = None) -> StoredObject:
        from app.services.hashing import sha256_bytes

        digest = sha256_bytes(body)
        extra = {"ContentType": content_type} if content_type else {}
        self._client.put_object(Bucket=self.private_bucket, Key=key, Body=body, **extra)
        return StoredObject(
            bucket=self.private_bucket,
            key=key,
            byte_size=len(body),
            sha256=digest,
            content_type=content_type,
        )

    def put_public_json(self, key: str, payload: dict) -> StoredObject:
        from app.services.hashing import sha256_bytes
        import json

        body = json.dumps(payload, indent=2, sort_keys=True).encode("utf-8")
        digest = sha256_bytes(body)
        self._client.put_object(
            Bucket=self.public_bucket,
            Key=key,
            Body=body,
            ContentType="application/json",
        )
        return StoredObject(
            bucket=self.public_bucket,
            key=key,
            byte_size=len(body),
            sha256=digest,
            content_type="application/json",
        )

    def get_object(self, bucket: str, key: str) -> bytes:
        resp = self._client.get_object(Bucket=bucket, Key=key)
        return resp["Body"].read()


_store: ObjectStore | None = None


def get_object_store() -> ObjectStore:
    global _store
    if _store is None:
        _store = ObjectStore()
        # Best-effort idempotent bucket bootstrap. Failures here are non-fatal
        # because the docker-compose bootstrap container handles it too.
        try:
            _store.ensure_buckets()
        except Exception:
            pass
    return _store


def evidence_key(organization_id, asset_id, evidence_id, filename: str) -> str:
    return safe_storage_key(
        "organizations",
        str(organization_id),
        "assets",
        str(asset_id),
        "raw",
        f"{evidence_id}_{os.path.basename(filename)}",
    )


def manifest_key(organization_id, asset_id, version: int) -> str:
    return safe_storage_key(
        "organizations",
        str(organization_id),
        "assets",
        str(asset_id),
        "manifests",
        f"manifest_v{version}.json",
    )


def public_verify_key(slug: str) -> str:
    return safe_storage_key("verification", slug, "deed-public.json")
