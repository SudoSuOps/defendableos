"""Draft-deed lifecycle correctness · the doctrine catching its own product.

These tests lock in the rule the user found by reading their own first published
record: a draft deed must NEVER render or serialize as if it were issued.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from types import SimpleNamespace

from app.models.deed import DeedStatus
from app.services.deed import (
    DRAFT_DISCLAIMER,
    hard_block_real_publication,
    is_draft_deed,
    render_public_preview,
)


def _draft_deed_fixture(
    *,
    record_status: str = "DRAFT_REVIEW_RECORD",
    issued_at: str | None = None,
    ens_status: str = "RESERVED_NOT_ISSUED",
    value_status: str = "WITHHELD_PENDING_VALIDATOR_REVIEW",
    validator_status: str = "PASSED_FOR_PACKAGING",
):
    """Build a draft-deed-shaped object with the fields render_public_preview reads."""
    deed_json = {
        "deed_type": "DEFENDABLE_DEED",
        "deed_version": "0.1",
        "record_status": record_status,
        "issued_at": issued_at,
        "asset": {
            "asset_reference": "DOV-COMPUTE-000001",
            "manufacturer": "NVIDIA",
            "model": "RTX PRO 6000 Blackwell",
            # private fields that the filter MUST strip
            "serial_number": "SN-SHOULD-NEVER-LEAK",
            "purchase_cost_private": 7250.00,
        },
        "evidence_packet": {
            "manifest_id": "00000000-0000-0000-0000-000000000000",
            "manifest_sha256": "deadbeef" * 8,
            "evidence_item_count": 3,
            "public_evidence_disclosure": "PRIVATE_EVIDENCE_REFERENCED_BY_HASH_ONLY",
            "private_filenames": ["should-be-stripped.pdf"],
        },
        "aiov_analysis": {
            "analysis_id": "abc-123",
            "status": "GENERATED_FOR_VALIDATOR_REVIEW",
            "value_display_status": value_status,
            "narrative": "private notes that must not leak",
        },
        "validator_review": {
            "protocol": "VALIDATE_THE_VALIDATOR",
            "receipt_id": "xyz-789",
            "status": validator_status,
            "receipt_sha256": "cafe" * 16,
        },
        "ens_identity": {
            "name": "ddeed-dov-compute-000001.swarmbee.defendable.eth",
            "status": ens_status,
            "public_resolution_target": None,
            "parent_organization_ens": "swarmbee.defendable.eth",
        },
        "disclosures": {
            "ai_assisted_record": True,
            "professional_appraisal": False,
            "legal_certification": False,
            "authentication_guarantee": False,
            "disclaimer": "old disclaimer that should be replaced by the canonical one",
        },
    }
    deed = SimpleNamespace(
        id=uuid.uuid4(),
        status=DeedStatus.DRAFT_REVIEW_RECORD,
        deed_json=deed_json,
        record_hash="cafe" * 16,
        created_at=datetime(2026, 5, 22, 16, 29, 45, tzinfo=timezone.utc),
        deed_reference="DDEED-DOV-COMPUTE-000001-v1",
        public_slug=None,
        is_public=False,
    )
    return deed


# ──────────────────────────────────────────────────────────────────────────
# (1) Draft records render as Public Preview only · issued_at is null
# ──────────────────────────────────────────────────────────────────────────
def test_draft_record_issued_at_is_null():
    deed = _draft_deed_fixture()
    pub = render_public_preview(deed)
    assert pub["issued_at"] is None, "draft deeds must NEVER have issued_at populated in public output"


def test_draft_record_has_created_at_from_db_row():
    deed = _draft_deed_fixture()
    pub = render_public_preview(deed)
    assert pub.get("created_at") == deed.created_at.isoformat()


# ──────────────────────────────────────────────────────────────────────────
# (2) Draft records cannot show PASSED_FOR_PACKAGING in their embedded validator
# ──────────────────────────────────────────────────────────────────────────
def test_draft_record_rewrites_validator_status():
    deed = _draft_deed_fixture(validator_status="PASSED_FOR_PACKAGING")
    pub = render_public_preview(deed)
    assert pub["validator_review"]["status"] == "PASSED_FOR_DRAFT_PACKAGING"
    assert pub["validator_review"]["human_approval_required"] is True


# ──────────────────────────────────────────────────────────────────────────
# (3) Draft records emit doctrine-correct publication_policy + disclosures
# ──────────────────────────────────────────────────────────────────────────
def test_draft_record_publication_policy_is_not_published():
    deed = _draft_deed_fixture()
    pub = render_public_preview(deed)
    pp = pub["publication_policy"]
    assert pp["public_verification_status"] == "NOT_PUBLISHED"
    assert pp["ens_published"] is False
    assert pp["value_claim_public"] is False
    assert pp["publication_requires_human_approval"] is True
    assert pp["public_preview_allowed"] is True


def test_draft_record_disclosures_have_no_issuance():
    deed = _draft_deed_fixture()
    pub = render_public_preview(deed)
    d = pub["disclosures"]
    assert d["final_valuation_issued"] is False
    assert d["deed_issued"] is False
    assert d["professional_appraisal"] is False
    assert d["legal_certification"] is False
    assert d["authentication_guarantee"] is False
    assert d["disclaimer"] == DRAFT_DISCLAIMER, "draft disclaimer must be the canonical text"


def test_draft_record_aiov_valuation_not_issued():
    deed = _draft_deed_fixture()
    pub = render_public_preview(deed)
    assert pub["aiov_analysis"]["valuation_issued"] is False


# ──────────────────────────────────────────────────────────────────────────
# (4) Integrity block · hash algorithm + canonicalization are explicit
# ──────────────────────────────────────────────────────────────────────────
def test_record_hash_lives_under_integrity_block():
    deed = _draft_deed_fixture()
    pub = render_public_preview(deed)
    integrity = pub["integrity"]
    assert integrity["hash_algorithm"] == "SHA-256"
    assert integrity["canonicalization"] == "DEFENDABLE_CANONICAL_JSON_V1"
    assert integrity["record_hash"]  # present and non-empty


def test_no_bare_top_level_record_hash():
    deed = _draft_deed_fixture()
    pub = render_public_preview(deed)
    # The bare top-level record_hash field must be moved under integrity.
    assert "record_hash" not in pub


# ──────────────────────────────────────────────────────────────────────────
# (5) Private evidence MUST NEVER leak through the public preview
# ──────────────────────────────────────────────────────────────────────────
def test_public_preview_strips_private_fields():
    deed = _draft_deed_fixture()
    pub = render_public_preview(deed)
    asset = pub["asset"]
    assert "serial_number" not in asset
    assert "purchase_cost_private" not in asset
    assert "purchase_cost" not in asset
    assert "private_filenames" not in pub["evidence_packet"]
    assert "narrative" not in pub["aiov_analysis"]


# ──────────────────────────────────────────────────────────────────────────
# (6) is_draft_deed conservative detection · ANY of 4 conditions → draft
# ──────────────────────────────────────────────────────────────────────────
def test_is_draft_when_record_status_is_draft():
    deed = _draft_deed_fixture(record_status="DRAFT_REVIEW_RECORD", issued_at="2026-05-22T00:00:00Z",
                               ens_status="ISSUED_OFFCHAIN", value_status="REVIEWED_AND_DISCLOSED")
    assert is_draft_deed(deed) is True


def test_is_draft_when_issued_at_null():
    deed = _draft_deed_fixture(record_status="APPROVED_FOR_PUBLIC", issued_at=None,
                               ens_status="ISSUED_OFFCHAIN", value_status="REVIEWED_AND_DISCLOSED")
    assert is_draft_deed(deed) is True


def test_is_draft_when_ens_reserved_not_issued():
    deed = _draft_deed_fixture(record_status="APPROVED_FOR_PUBLIC", issued_at="2026-05-22T00:00:00Z",
                               ens_status="RESERVED_NOT_ISSUED", value_status="REVIEWED_AND_DISCLOSED")
    assert is_draft_deed(deed) is True


def test_is_draft_when_value_withheld():
    deed = _draft_deed_fixture(record_status="APPROVED_FOR_PUBLIC", issued_at="2026-05-22T00:00:00Z",
                               ens_status="ISSUED_OFFCHAIN", value_status="WITHHELD_PENDING_VALIDATOR_REVIEW")
    assert is_draft_deed(deed) is True


# ──────────────────────────────────────────────────────────────────────────
# (7) Hard-block · real publication refused while any draft condition holds
# ──────────────────────────────────────────────────────────────────────────
def test_hard_block_lists_all_draft_reasons():
    deed = _draft_deed_fixture()  # default fixture has ALL four conditions true
    blocked, reasons = hard_block_real_publication(deed)
    assert blocked is True
    assert "record_status is DRAFT_REVIEW_RECORD" in reasons
    assert "issued_at is null" in reasons
    assert "ENS status is RESERVED_NOT_ISSUED" in reasons
    assert "value_display_status is WITHHELD_PENDING_VALIDATOR_REVIEW" in reasons


def test_hard_block_clears_when_all_conditions_clear():
    deed = _draft_deed_fixture(
        record_status="APPROVED_FOR_PUBLIC",
        issued_at="2026-05-22T18:00:00Z",
        ens_status="ISSUED_OFFCHAIN",
        value_status="REVIEWED_AND_DISCLOSED",
    )
    deed.status = DeedStatus.APPROVED_FOR_PUBLIC
    blocked, reasons = hard_block_real_publication(deed)
    assert blocked is False
    assert reasons == []


# ──────────────────────────────────────────────────────────────────────────
# (8) Lifecycle output matches the doctrine canonical labels
# ──────────────────────────────────────────────────────────────────────────
def test_draft_renders_canonical_record_status():
    deed = _draft_deed_fixture()
    pub = render_public_preview(deed)
    assert pub["record_status"] == "DRAFT_REVIEW_RECORD"


def test_legacy_approved_deed_with_draft_data_still_renders_as_draft():
    """A deed whose status was prematurely flipped to APPROVED_FOR_PUBLIC by
    the old publish flow MUST still render as draft until the four conditions
    clear. This is the exact bug the user found in their own first record."""
    deed = _draft_deed_fixture()
    # Simulate the legacy publish having flipped the status:
    deed.status = DeedStatus.APPROVED_FOR_PUBLIC
    pub = render_public_preview(deed)
    assert pub["record_status"] == "DRAFT_REVIEW_RECORD"
    assert pub["issued_at"] is None
    assert pub["validator_review"]["status"] == "PASSED_FOR_DRAFT_PACKAGING"
    assert pub["publication_policy"]["public_verification_status"] == "NOT_PUBLISHED"
