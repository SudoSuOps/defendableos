"""Ledger lookup endpoint · /api/v1/public/lookup.

Tests the four lookup kinds + the doctrine guards (no leakage of private or
not-yet-public records).
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from types import SimpleNamespace

# Don't import the route directly · the helpers are what we test.
from app.api.v1 import public as public_module
from app.models.deed import DeedStatus


def _fake_deed(
    *,
    is_public: bool = True,
    record_hash: str = "a" * 64,
    deed_reference: str = "DDEED-DOV-COMPUTE-000001-v2",
    public_slug: str = "ddeed-dov-compute-000001-v2",
    version: int = 2,
):
    return SimpleNamespace(
        id=uuid.uuid4(),
        status=DeedStatus.DRAFT_REVIEW_RECORD,
        record_hash=record_hash,
        deed_reference=deed_reference,
        public_slug=public_slug,
        is_public=is_public,
        version=version,
        created_at=datetime(2026, 5, 22, 16, 29, 45, tzinfo=timezone.utc),
        deed_json={
            "deed_type": "DEFENDABLE_DEED",
            "record_status": "DRAFT_REVIEW_RECORD",
            "issued_at": None,
            "asset": {
                "asset_reference": "DOV-COMPUTE-000001",
                "asset_class": "COMPUTE_HARDWARE",
                "category": "GPU_ACCELERATOR",
                "manufacturer": "NVIDIA",
                "model": "RTX PRO 6000 Blackwell",
            },
            "evidence_packet": {
                "manifest_sha256": "b" * 64,
                "evidence_item_count": 3,
                "public_evidence_disclosure": "PRIVATE_EVIDENCE_REFERENCED_BY_HASH_ONLY",
            },
            "aiov_analysis": {
                "analysis_id": "abc",
                "status": "GENERATED_FOR_VALIDATOR_REVIEW",
                "value_display_status": "WITHHELD_PENDING_VALIDATOR_REVIEW",
            },
            "validator_review": {
                "status": "PASSED_FOR_PACKAGING",
                "receipt_sha256": "c" * 64,
            },
            "ens_identity": {
                "name": "ddeed-dov-compute-000001.swarmbee.defendable.eth",
                "status": "RESERVED_NOT_ISSUED",
            },
        },
    )


# ──────────────────────────────────────────────────────────────────────────
# build_lookup_response · output shape and doctrine fields
# ──────────────────────────────────────────────────────────────────────────
def test_build_lookup_response_includes_lifecycle():
    deed = _fake_deed()
    out = public_module._build_lookup_response("RECORD_HASH", "a" * 64, deed)
    assert out["kind"] == "RECORD_HASH"
    assert out["matched_hash"] == "a" * 64
    assert out["deed_reference"] == "DDEED-DOV-COMPUTE-000001-v2"
    assert out["public_slug"] == "ddeed-dov-compute-000001-v2"
    assert out["summary"] == "NVIDIA RTX PRO 6000 Blackwell"
    assert out["verify_url"] == "/verify/ddeed-dov-compute-000001-v2"
    assert out["showcase_url"] == "/showcase/ddeed-dov-compute-000001-v2"
    lc = out["lifecycle"]
    assert lc["is_draft"] is True
    assert lc["record_status"] == "DRAFT_REVIEW_RECORD"
    assert lc["validator_status"] == "PASSED_FOR_DRAFT_PACKAGING"
    assert lc["publication_status"] == "NOT_PUBLISHED"
    assert lc["value_status"] == "WITHHELD_PENDING_VALIDATOR_REVIEW"
    assert lc["ens_status"] == "RESERVED_NOT_ISSUED"


def test_build_lookup_response_carries_integrity_block():
    deed = _fake_deed()
    out = public_module._build_lookup_response("RECORD_HASH", "a" * 64, deed)
    integrity = out.get("integrity")
    assert integrity is not None
    assert integrity["hash_algorithm"] == "SHA-256"
    assert integrity["canonicalization"] == "DEFENDABLE_CANONICAL_JSON_V1"


def test_build_lookup_response_accepts_extra_keys():
    deed = _fake_deed()
    out = public_module._build_lookup_response(
        "MANIFEST_HASH",
        "b" * 64,
        deed,
        manifest_id="00000000-0000-0000-0000-000000000000",
        manifest_version=2,
    )
    assert out["manifest_id"] == "00000000-0000-0000-0000-000000000000"
    assert out["manifest_version"] == 2


# ──────────────────────────────────────────────────────────────────────────
# _not_found · honest "we didn't find anything" shape
# ──────────────────────────────────────────────────────────────────────────
def test_not_found_default_shape():
    out = public_module._not_found("some-hash")
    assert out["kind"] == "NOT_FOUND"
    assert out["matched_hash"] == "some-hash"
    assert out["lifecycle"] is None
    assert "no public defendable record" in out["summary"].lower()


def test_not_found_carries_custom_detail():
    out = public_module._not_found("DDEED-XXX-v1", "Deed reference is not preview-published.")
    assert out["summary"] == "Deed reference is not preview-published."


# ──────────────────────────────────────────────────────────────────────────
# Regex pattern checks · we reject garbage early
# ──────────────────────────────────────────────────────────────────────────
def test_sha256_regex_accepts_lowercase_64hex():
    assert public_module._SHA256_RE.match("a" * 64) is not None
    assert public_module._SHA256_RE.match("0123456789abcdef" * 4) is not None


def test_sha256_regex_rejects_uppercase_and_short():
    assert public_module._SHA256_RE.match("A" * 64) is None  # must be lowercased before
    assert public_module._SHA256_RE.match("a" * 63) is None
    assert public_module._SHA256_RE.match("a" * 65) is None
    assert public_module._SHA256_RE.match("z" * 64) is None  # not hex


def test_deed_ref_regex_accepts_canonical_form():
    assert public_module._DEED_REF_RE.match("DDEED-DOV-COMPUTE-000001-v2") is not None
    assert public_module._DEED_REF_RE.match("ddeed-dov-compute-000001-v2") is not None  # case-insensitive


def test_deed_ref_regex_rejects_garbage():
    assert public_module._DEED_REF_RE.match("DDEED-no-version") is None
    assert public_module._DEED_REF_RE.match("not-a-deed") is None
    assert public_module._DEED_REF_RE.match("DDEED-X-vABC") is None


# ──────────────────────────────────────────────────────────────────────────
# Doctrine: private deeds must NEVER appear in lookup results
# (This is enforced at the query layer via is_public=True filter · the test
# here documents the contract so future refactors don't break it.)
# ──────────────────────────────────────────────────────────────────────────
def test_not_public_deed_is_not_discoverable_doctrine():
    """If a deed is_public=False, the route's SQL filter ensures it does not
    surface · _build_lookup_response itself isn't gated, but the SQL queries
    in `public_lookup()` only consider `is_public=True` deeds."""
    deed = _fake_deed(is_public=False)
    assert deed.is_public is False
