"""Claw Bakery storage abstraction.

Two drivers:
  · local    · plain filesystem rooted at CLAW_BAKERY_LOCAL_ROOT
  · s3       · S3-compatible (Tigris / R2 / MinIO / AWS) via boto3

Doctrine guarantees:
  · Raw evidence is write-once. write_raw() refuses to overwrite an
    existing key; the caller must construct a new key (typically by
    appending a UUID suffix) if a write fails with KeyExistsError.
  · Redacted copies are SEPARATE artifacts under redacted/* prefixes.
  · Every put returns a SHA-256 digest and byte size · the receipt
    layer hashes again from the stored bytes to verify.
  · No secret values are written to logs. The store records only
    bucket + key + sha256 + byte_size in any debug surface.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from app.core.config import settings


_SAFE_KEY_PART = re.compile(r"[^A-Za-z0-9._\-]")
_BAKERY_KEY_PREFIX = "claw-bakery"


class KeyExistsError(IOError):
    """Raised when a write would overwrite an existing raw-evidence artifact."""


def safe_key_part(part: str) -> str:
    """Sanitise a single path component for use in a storage key."""
    if not part:
        raise ValueError("empty key part")
    if ".." in part or part.startswith("/") or part.startswith("\\"):
        raise ValueError(f"unsafe path part: {part!r}")
    return _SAFE_KEY_PART.sub("_", part)


def bakery_key(*parts: str) -> str:
    """Build a Claw-Bakery-prefixed storage key from path components.

    The first component must be one of the known top-level bakery
    directories (raw-evidence, redacted, pair-candidates, ...). The
    function does not validate this · the directory enum check happens
    higher up at the caller layer (BakeryStore methods).
    """
    cleaned = [safe_key_part(p) for p in parts if p]
    return "/".join([_BAKERY_KEY_PREFIX, *cleaned])


# Canonical top-level bakery directories (mirrored 1:1 in local + s3).
BAKERY_DIRS = (
    "raw-evidence/intakes",
    "raw-evidence/snapshots",
    "raw-evidence/validator-reviews",
    "redacted/approved-for-evaluation",
    "redacted/approved-for-training",
    "pair-candidates/pending",
    "pair-candidates/honey",
    "pair-candidates/jelly",
    "pair-candidates/jelly-repaired",
    "pair-candidates/propolis-failures",
    "pair-candidates/quarantined",
    # Compute Market Watch · sold-comp evidence tribunal
    "compute-market-watch/sold-comps/honey",
    "compute-market-watch/sold-comps/jelly",
    "compute-market-watch/sold-comps/propolis",
    "compute-market-watch/sold-comps/quarantined",
    "compute-market-watch/ingest-runs",
    "benchmark-packs",
    "holdouts/sealed",
    "holdouts/manifests",
    "dataset-releases",
    "receipts/sha256",
    "receipts/manifests",
    "receipts/merkle-ready",
    "deeds/draft",
    "deeds/eligible",
    "deeds/issued",
    "deeds/denied",
    "events",
)


@dataclass
class StoredArtifact:
    key: str
    byte_size: int
    sha256: str
    content_type: str
    driver: str
    created_at: str  # ISO-8601


# ─── Driver interface ─────────────────────────────────────────────────


class BakeryDriver:
    name: str

    def write_immutable(self, key: str, body: bytes, content_type: str) -> StoredArtifact:
        raise NotImplementedError

    def write_overwrite(self, key: str, body: bytes, content_type: str) -> StoredArtifact:
        raise NotImplementedError

    def read(self, key: str) -> bytes:
        raise NotImplementedError

    def exists(self, key: str) -> bool:
        raise NotImplementedError

    def list_keys(self, prefix: str) -> list[str]:
        raise NotImplementedError


class LocalDriver(BakeryDriver):
    name = "local"

    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)
        for d in BAKERY_DIRS:
            (self.root / d).mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        # `key` is already _BAKERY_KEY_PREFIX/.../... so strip the prefix
        if not key.startswith(_BAKERY_KEY_PREFIX + "/"):
            raise ValueError(f"key must start with {_BAKERY_KEY_PREFIX!r}/")
        rel = key[len(_BAKERY_KEY_PREFIX) + 1:]
        return self.root / rel

    def write_immutable(self, key: str, body: bytes, content_type: str) -> StoredArtifact:
        p = self._path(key)
        if p.exists():
            raise KeyExistsError(f"refuse overwrite: {key}")
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("xb") as f:  # exclusive create · raises if exists between check + open
            f.write(body)
        return self._artifact(key, body, content_type)

    def write_overwrite(self, key: str, body: bytes, content_type: str) -> StoredArtifact:
        p = self._path(key)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(body)
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
                out.append(f"{_BAKERY_KEY_PREFIX}/{rel.as_posix()}")
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


class S3Driver(BakeryDriver):
    """S3-compatible driver. Uses the existing ObjectStore bucket layout
    and prefixes everything with claw-bakery/. The private-evidence
    bucket is the home for all bakery artifacts · public exposure is
    handled by an explicit dataset-release step (not by this driver).
    """
    name = "s3"

    def __init__(self) -> None:
        # Lazy boto3 import · keeps test-time isolation lighter
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
            raise KeyExistsError(f"refuse overwrite: {key}")
        return self.write_overwrite(key, body, content_type)

    def write_overwrite(self, key: str, body: bytes, content_type: str) -> StoredArtifact:
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


# ─── Public facade ────────────────────────────────────────────────────


class BakeryStore:
    """High-level immutable-write API for the Claw Bakery pipeline."""

    def __init__(self, driver: BakeryDriver) -> None:
        self.driver = driver

    # ── Raw evidence (write-once) ──────────────────────────────────────

    def put_raw_intake(self, run_id: str, payload: dict[str, Any]) -> StoredArtifact:
        body = json.dumps(payload, sort_keys=True, indent=2).encode("utf-8")
        key = bakery_key("raw-evidence", "intakes", f"{safe_key_part(run_id)}.json")
        return self.driver.write_immutable(key, body, "application/json")

    def put_raw_snapshot(self, run_id: str, payload: dict[str, Any]) -> StoredArtifact:
        body = json.dumps(payload, sort_keys=True, indent=2).encode("utf-8")
        key = bakery_key("raw-evidence", "snapshots", f"{safe_key_part(run_id)}.json")
        return self.driver.write_immutable(key, body, "application/json")

    # ── Redacted / derived (separate objects, never replacing raw) ─────

    def put_redacted_for_evaluation(self, run_id: str, payload: dict[str, Any]) -> StoredArtifact:
        body = json.dumps(payload, sort_keys=True, indent=2).encode("utf-8")
        key = bakery_key("redacted", "approved-for-evaluation", f"{safe_key_part(run_id)}.json")
        return self.driver.write_immutable(key, body, "application/json")

    def put_redacted_for_training(self, run_id: str, payload: dict[str, Any]) -> StoredArtifact:
        body = json.dumps(payload, sort_keys=True, indent=2).encode("utf-8")
        key = bakery_key("redacted", "approved-for-training", f"{safe_key_part(run_id)}.json")
        return self.driver.write_immutable(key, body, "application/json")

    # ── Pair candidates (mutable bucket per label) ─────────────────────

    def put_pair_candidate(
        self,
        *,
        pair_id: str,
        bucket: Literal[
            "pending", "honey", "jelly", "jelly-repaired",
            "propolis-failures", "quarantined",
        ],
        payload: dict[str, Any],
    ) -> StoredArtifact:
        body = json.dumps(payload, sort_keys=True, indent=2).encode("utf-8")
        key = bakery_key("pair-candidates", bucket, f"{safe_key_part(pair_id)}.json")
        return self.driver.write_overwrite(key, body, "application/json")

    # ── Receipts ───────────────────────────────────────────────────────

    def put_receipt(self, receipt_id: str, payload: dict[str, Any]) -> StoredArtifact:
        body = json.dumps(payload, sort_keys=True, indent=2).encode("utf-8")
        key = bakery_key("receipts", "sha256", f"{safe_key_part(receipt_id)}.json")
        return self.driver.write_immutable(key, body, "application/json")

    def put_manifest(self, manifest_id: str, payload: dict[str, Any]) -> StoredArtifact:
        body = json.dumps(payload, sort_keys=True, indent=2).encode("utf-8")
        key = bakery_key("receipts", "manifests", f"{safe_key_part(manifest_id)}.json")
        return self.driver.write_immutable(key, body, "application/json")

    # ── Dataset releases ───────────────────────────────────────────────

    def put_dataset_release(self, dataset_id: str, version: str, payload: dict[str, Any]) -> StoredArtifact:
        body = json.dumps(payload, sort_keys=True, indent=2).encode("utf-8")
        key = bakery_key("dataset-releases", f"{safe_key_part(dataset_id)}_{safe_key_part(version)}.json")
        return self.driver.write_immutable(key, body, "application/json")

    # ── Events outbox ──────────────────────────────────────────────────

    def append_event(self, event_id: str, payload: dict[str, Any]) -> StoredArtifact:
        body = json.dumps(payload, sort_keys=True, indent=2).encode("utf-8")
        key = bakery_key("events", f"{safe_key_part(event_id)}.json")
        return self.driver.write_immutable(key, body, "application/json")

    # ── Read helpers ───────────────────────────────────────────────────

    def read_json(self, key: str) -> dict[str, Any]:
        return json.loads(self.driver.read(key).decode("utf-8"))

    def list_under(self, prefix: str) -> list[str]:
        # Accept multi-segment prefixes (e.g. "raw-evidence/intakes") by
        # splitting and re-sanitising each segment.
        parts = [p for p in prefix.split("/") if p]
        return self.driver.list_keys(bakery_key(*parts))

    def list_pair_candidates(self, bucket: str) -> list[str]:
        return self.driver.list_keys(bakery_key("pair-candidates", bucket))


# ─── Singleton factory ────────────────────────────────────────────────


_store: BakeryStore | None = None


def _resolve_local_root() -> Path:
    env_root = os.environ.get("CLAW_BAKERY_LOCAL_ROOT")
    if env_root:
        return Path(env_root).expanduser().resolve()
    # Default sits inside the repo's data/ tree alongside other dev artifacts.
    return Path(os.environ.get("CLAW_BAKERY_DEFAULT_ROOT",
                                "./data/claw-bakery")).expanduser().resolve()


def get_bakery_store() -> BakeryStore:
    global _store
    if _store is not None:
        return _store
    driver_name = os.environ.get("CLAW_BAKERY_STORAGE_DRIVER", "local").lower()
    if driver_name == "s3":
        _store = BakeryStore(S3Driver())
    else:
        _store = BakeryStore(LocalDriver(_resolve_local_root()))
    return _store


def reset_bakery_store_for_tests(root: Path | None = None) -> BakeryStore:
    """Reset the singleton · used by pytest fixtures only."""
    global _store
    if root is None:
        root = Path(os.environ.get("CLAW_BAKERY_LOCAL_ROOT", "./data/claw-bakery")).expanduser().resolve()
    _store = BakeryStore(LocalDriver(root))
    return _store
