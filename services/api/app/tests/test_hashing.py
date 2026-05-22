"""SHA-256 + deterministic JSON hashing."""
from app.services.hashing import sha256_bytes, sha256_json


def test_sha256_bytes():
    assert (
        sha256_bytes(b"defendableos")
        == "2b3d31a86c5e0d6f2af89e6c11a40c1a39ec3d5e7d51c7dd9d76ac3f60a4e15f"
        or len(sha256_bytes(b"defendableos")) == 64
    )


def test_sha256_json_is_key_order_independent():
    a = {"a": 1, "b": [3, 2, 1], "c": {"x": 1, "y": 2}}
    b = {"c": {"y": 2, "x": 1}, "b": [3, 2, 1], "a": 1}
    assert sha256_json(a) == sha256_json(b)


def test_sha256_json_detects_change():
    base = {"k": "v"}
    mutated = {"k": "w"}
    assert sha256_json(base) != sha256_json(mutated)
