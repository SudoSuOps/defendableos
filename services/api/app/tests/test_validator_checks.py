"""Deterministic validator checks · don't pass blocking findings silently."""
from app.services.validator_checks import CHECKS, summarise, CheckResult


def test_check_identifiers_stable():
    # If a check is renamed downstream UI will break · this test is the canary.
    assert "ASSET_IDENTITY_HAS_SUPPORTING_EVIDENCE" in CHECKS
    assert "LISTING_PRICES_NOT_PRESENTED_AS_CONFIRMED_SALES" in CHECKS
    assert "PUBLIC_DEED_CONTAINS_NO_PRIVATE_DOCUMENT_DATA" in CHECKS
    assert len(CHECKS) == 12


def test_blocking_failure_summarises_repair():
    results = [
        CheckResult(check="ASSET_IDENTITY_HAS_SUPPORTING_EVIDENCE", status="FAIL", severity="BLOCKING"),
        CheckResult(check="EVIDENCE_MANIFEST_EXISTS", status="PASS"),
    ]
    assert summarise(results) == "FAILED_REQUIRES_REPAIR"


def test_all_pass_summarises_packaging():
    results = [CheckResult(check=c, status="PASS") for c in CHECKS]
    assert summarise(results) == "PASSED_FOR_PACKAGING"


def test_pass_with_flag_does_not_block_packaging():
    results = [
        CheckResult(check=CHECKS[0], status="PASS"),
        CheckResult(check=CHECKS[5], status="PASS_WITH_FLAG", severity="MEDIUM"),
    ]
    assert summarise(results) == "PASSED_FOR_PACKAGING"
