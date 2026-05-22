"""SHA-256 helpers · evidence is the permanent record."""
from __future__ import annotations

import hashlib
import json
from typing import Any


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_stream(stream) -> tuple[str, int]:
    """Hash a file-like stream while counting bytes. Returns (hex_digest, byte_count)."""
    h = hashlib.sha256()
    total = 0
    while True:
        chunk = stream.read(1 << 20)  # 1 MiB
        if not chunk:
            break
        h.update(chunk)
        total += len(chunk)
    return h.hexdigest(), total


def sha256_json(obj: Any) -> str:
    """Deterministic hashing of a JSON-serialisable object · sorted keys, compact."""
    encoded = json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
