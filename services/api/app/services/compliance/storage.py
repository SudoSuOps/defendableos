"""Compliance storage · parallel to bakery_storage but rooted at `compliance/`.

Two drivers · same contract as bakery_storage:
  · local    · plain filesystem rooted at COMPLIANCE_LOCAL_ROOT
  · s3       · S3-compatible (Tigris / R2 / MinIO / AWS) via boto3

Doctrine guarantees mirror the bakery (immutable raw writes, separate
redacted copies, SHA-256 receipts, no secrets in logs) · the difference
is regulatory scope: compliance artifacts must be auditable by a regulator
without leaking any bakery/operational evidence.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.core.config import settings


_SAFE_KEY_PART = re.compile(r"[^A-Za-z0-9._\-]")
_COMPLIANCE_KEY_PREFIX = "compliance"


class ComplianceKeyExistsError(IOError):
    """Raised when a write would overwrite an existing compliance artifact."""


def safe_key_part(part: str) -> str:
    if not part:
        raise ValueError("empty key part")
    if ".." in part or part.startswith("/") or part.startswith("\\"):
        raise ValueError(f"unsafe path part: {part!r}")
    return _SAFE_KEY_PART.sub("_", part)


def compliance_key(*parts: str) -> str:
    cleaned = [safe_key_part(p) for p in parts if p]
    return "/".join([_COMPLIANCE_KEY_PREFIX, *cleaned])


# Canonical top-level compliance directories
COMPLIANCE_DIRS = (
    "ebay/account-deletion/raw-notifications",
    "ebay/account-deletion/receipts",
    "ebay/account-deletion/review-queue",
    "ebay/account-deletion/completed-actions",
    "ebay/account-deletion/events",
    "ebay/account-deletion/idempotency",
)


@dataclass
class StoredArtifact:
    key: str
    byte_size: int
    sha256: str
    content_type: str
    driver: str
    created_at: str


# ─── Driver protocol ────────────────────────────────────────────────


class ComplianceDriver:
    name: str

    def write_immutable(self, key: str, body: bytes, content_type: str) -> StoredArtifact:
        raise NotImplementedError

    def read(self, key: str) -> bytes:
        raise NotImplementedError

    def exists(self, key: str) -> bool:
        raise NotImplementedError

    def list_keys(self, prefix: str) -> list[str]:
        raise NotImplementedError


class LocalDriver(ComplianceDriver):
    name = "local"

    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)
        for d in COMPLIANCE_DIRS:
            (self.root / d).mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        if not key.startswith(_COMPLIANCE_KEY_PREFIX + "/"):
            raise ValueError(f"key must start with {_COMPLIANCE_KEY_PREFIX!r}/")
        rel = key[len(_COMPLIANCE_KEY_PREFIX) + 1:]
        return self.root / rel

    def write_immutable(self, key: str, body: bytes, content_type: str) -> StoredArtifact:
        p = self._path(key)
        if p.exists():
            raise ComplianceKeyExistsError(f"refuse overwrite: {key}")
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("xb") as f:
            f.write(body)
        return self._artifact(key, body, content_type)

    def read(self, key: str) -> bytes:
        return self._path(key).read_bytes()

    def exists(self, key: str) -> bool:
        return self._path(key).exists()

    def list_keys(self, prefix: str) -> list[str]:
        base = self._path(prefix)
        if not base.exists() or not base.is_dir():
            return []
        out: list[str] = []
        for p in base.rglob("*"):
            if p.is_file():
                rel = p.relative_to(self.root)
                out.append(f"{_COMPLIANCE_KEY_PREFIX}/{rel.as_posix()}")
        return sorted(out)

    def _artifact(self, key: str, body: bytes, content_type: str) -> StoredArtifact:
        return StoredArtifact(
            key=key,
            byte_size=len(body),
            sha256=hashlib.sha256(body).hexdigest(),
            content_type=content_type,
            driver=self.name,
            created_at=datetime.now(timezone.utc).isoformat(),
        )


class S3Driver(ComplianceDriver):
    name = "s3"

    def __init__(self) -> None:
        import boto3
        from botocore.client import Config
        self._client = boto3.client(
            "s3",
            endpoint_url=settings.s3_endpoint_url,
            aws_access_key_id=settings.s3_access_key_id,
            aws_secret_access_key=settings.s3_secret_access_key,
            region_name=settings.s3_region,
            config=Config(signature_version="s3v4"),
        )
        self.bucket = settings.s3_private_evidence_bucket

    def write_immutable(self, key: str, body: bytes, content_type: str) -> StoredArtifact:
        if self.exists(key):
            raise ComplianceKeyExistsError(f"refuse overwrite: {key}")
        self._client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=body,
            ContentType=content_type,
        )
        return StoredArtifact(
            key=key,
            byte_size=len(body),
            sha256=hashlib.sha256(body).hexdigest(),
            content_type=content_type,
            driver=self.name,
            created_at=datetime.now(timezone.utc).isoformat(),
        )

    def read(self, key: str) -> bytes:
        resp = self._client.get_object(Bucket=self.bucket, Key=key)
        return resp["Body"].read()

    def exists(self, key: str) -> bool:
        try:
            self._client.head_object(Bucket=self.bucket, Key=key)
            return True
        except Exception:  # noqa: BLE001
            return False

    def list_keys(self, prefix: str) -> list[str]:
        paginator = self._client.get_paginator("list_objects_v2")
        out: list[str] = []
        for page in paginator.paginate(Bucket=self.bucket, Prefix=prefix):
            for obj in page.get("Contents", []) or []:
                out.append(obj["Key"])
        return sorted(out)


# ─── ComplianceStore facade ─────────────────────────────────────────


class ComplianceStore:
    def __init__(self, driver: ComplianceDriver) -> None:
        self.driver = driver

    # ── eBay account-deletion ──

    def put_raw_notification(self, event_id: str, payload: bytes) -> StoredArtifact:
        key = compliance_key("ebay", "account-deletion", "raw-notifications", f"{safe_key_part(event_id)}.json")
        return self.driver.write_immutable(key, payload, "application/json")

    def put_receipt(self, receipt_id: str, payload: dict[str, Any]) -> StoredArtifact:
        body = json.dumps(payload, sort_keys=True, indent=2).encode("utf-8")
        key = compliance_key("ebay", "account-deletion", "receipts", f"{safe_key_part(receipt_id)}.json")
        return self.driver.write_immutable(key, body, "application/json")

    def put_review_record(self, event_id: str, payload: dict[str, Any]) -> StoredArtifact:
        body = json.dumps(payload, sort_keys=True, indent=2).encode("utf-8")
        key = compliance_key("ebay", "account-deletion", "review-queue", f"{safe_key_part(event_id)}.json")
        return self.driver.write_immutable(key, body, "application/json")

    def put_completed_action(self, event_id: str, payload: dict[str, Any]) -> StoredArtifact:
        body = json.dumps(payload, sort_keys=True, indent=2).encode("utf-8")
        key = compliance_key("ebay", "account-deletion", "completed-actions", f"{safe_key_part(event_id)}.json")
        return self.driver.write_immutable(key, body, "application/json")

    def append_event(self, event_id: str, payload: dict[str, Any]) -> StoredArtifact:
        body = json.dumps(payload, sort_keys=True, indent=2).encode("utf-8")
        key = compliance_key("ebay", "account-deletion", "events", f"{safe_key_part(event_id)}.json")
        return self.driver.write_immutable(key, body, "application/json")

    def claim_idempotency(self, dedupe_id: str, payload: dict[str, Any]) -> tuple[bool, str]:
        """Reserve a slot for an event-id. Returns (was_fresh, key).

        Idempotency: if the dedupe_id has already been claimed, returns
        (False, existing_key) and does not write. If fresh, writes the
        marker and returns (True, new_key).
        """
        body = json.dumps(payload, sort_keys=True, indent=2).encode("utf-8")
        key = compliance_key("ebay", "account-deletion", "idempotency", f"{safe_key_part(dedupe_id)}.json")
        try:
            self.driver.write_immutable(key, body, "application/json")
            return True, key
        except ComplianceKeyExistsError:
            return False, key

    def read_json(self, key: str) -> dict[str, Any]:
        return json.loads(self.driver.read(key).decode("utf-8"))

    def list_under(self, prefix: str) -> list[str]:
        parts = [p for p in prefix.split("/") if p]
        return self.driver.list_keys(compliance_key(*parts))


# ─── Singleton factory ──────────────────────────────────────────────


_store: ComplianceStore | None = None


def _resolve_local_root() -> Path:
    env_root = os.environ.get("COMPLIANCE_LOCAL_ROOT")
    if env_root:
        return Path(env_root).expanduser().resolve()
    return Path(os.environ.get("COMPLIANCE_DEFAULT_ROOT", "./data/compliance")).expanduser().resolve()


def get_compliance_store() -> ComplianceStore:
    global _store
    if _store is not None:
        return _store
    driver_name = os.environ.get("COMPLIANCE_STORAGE_DRIVER", "local").lower()
    if driver_name == "s3":
        _store = ComplianceStore(S3Driver())
    else:
        _store = ComplianceStore(LocalDriver(_resolve_local_root()))
    return _store


def reset_compliance_store_for_tests() -> None:
    global _store
    _store = None
