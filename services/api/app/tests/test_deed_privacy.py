"""Critical test: public deed payload must NEVER contain private fields.

This test reflects the doctrine: "Public verification pages contain only
approved non-sensitive proof data."
"""
from app.services.deed import filter_public_payload


def test_filter_strips_private_fields():
    deed_json = {
        "deed_type": "DEFENDABLE_DEED",
        "deed_version": "0.1",
        "asset": {
            "asset_reference": "DOV-COMPUTE-000001",
            "manufacturer": "NVIDIA",
            "model": "RTX PRO 6000 Blackwell",
            # The next three lines simulate a buggy upstream that leaks privates.
            "serial_number": "SN-SHOULD-NEVER-LEAK-0001",
            "private_serial_number": "PRIV-9999",
            "purchase_cost_private": 7250.00,
        },
        "evidence_packet": {
            "manifest_id": "00000000-0000-0000-0000-000000000000",
            "manifest_sha256": "deadbeef",
            "evidence_item_count": 14,
            "public_evidence_disclosure": "PRIVATE_EVIDENCE_REFERENCED_BY_HASH_ONLY",
            "private_filenames": ["purchase_receipt.pdf", "owner_email.txt"],
        },
        "aiov_analysis": {
            "analysis_id": "abc",
            "status": "GENERATED_FOR_VALIDATOR_REVIEW",
            "narrative": "Private notes that should not be exposed publicly.",
        },
        "record_hash": "0xdeadbeef",
    }

    public = filter_public_payload(deed_json)

    # private fields stripped
    assert "serial_number" not in public["asset"]
    assert "private_serial_number" not in public["asset"]
    assert "purchase_cost_private" not in public["asset"]
    # evidence packet only exposes manifest_id / manifest_sha256 / evidence_item_count
    assert "private_filenames" not in public["evidence_packet"]
    # narrative stripped from aiov
    assert "narrative" not in public["aiov_analysis"]
    # safe fields preserved
    assert public["asset"]["asset_reference"] == "DOV-COMPUTE-000001"
    assert public["evidence_packet"]["manifest_sha256"] == "deadbeef"
    assert public["record_hash"] == "0xdeadbeef"
