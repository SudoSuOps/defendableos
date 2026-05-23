"""SHA-256 bundle manifest · matches the platform's hashing.py pipeline.

The manifest is sorted-key compact JSON keyed by relative filename →
SHA-256 hex. The manifest itself is then hashed to produce the
bundle hash that anchors downstream deed JSON.

Identical algorithm to services/api/app/services/hashing.py so the
integrity chain is uniform from edge capture through deed publication.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            block = f.read(chunk)
            if not block:
                break
            h.update(block)
    return h.hexdigest()


def sha256_json(obj: object) -> str:
    """Sorted-key compact JSON · matches platform deterministic hash."""
    payload = json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def build_bundle_manifest(run_dir: Path) -> dict[str, object]:
    """Hash every regular file in run_dir except manifest + public-safe.

    public_safe_attestation.json is EXCLUDED because it embeds the
    bundle hash itself · including it would create a chicken-and-egg
    where the hash refers to a stale version of the file. Operators
    verify public_safe_attestation.json by recomputing the bundle
    hash against the listed files.

    Returns dict with:
      · per_file_sha256: dict[str, str]   relative path → hash
      · bundle_sha256: str                 hash of sorted per_file map
    """
    per_file: dict[str, str] = {}
    for path in sorted(run_dir.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(run_dir).as_posix()
        if rel in {"manifest.sha256", "manifest.json", "public_safe_attestation.json"}:
            continue
        per_file[rel] = sha256_file(path)
    bundle_hash = sha256_json(per_file)
    return {
        "per_file_sha256": per_file,
        "bundle_sha256": bundle_hash,
        "hash_algorithm": "SHA-256",
        "manifest_excludes": ["manifest.sha256", "public_safe_attestation.json"],
    }


def write_manifest(run_dir: Path) -> dict[str, object]:
    """Compute and persist `manifest.sha256` in run_dir."""
    manifest = build_bundle_manifest(run_dir)
    (run_dir / "manifest.sha256").write_text(
        json.dumps(manifest, sort_keys=True, indent=2) + "\n"
    )
    return manifest
