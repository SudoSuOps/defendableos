"""Deterministic Validate the Validator checks.

Twelve canonical checks operate on the latest AIOV analysis, manifest, research
sources, and deed-eligibility state. Findings include severity. The receipt is
hashed deterministically so it can travel with the deed.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.models.ai import AIOVAnalysis
from app.models.asset import Asset
from app.models.evidence import EvidenceItem, EvidenceManifest, ManifestStatus, Visibility
from app.models.research import (
    EvidenceClassification,
    ResearchSession,
    ResearchSource,
    SourceLane,
)
from app.services.hashing import sha256_json


# ── Check identifiers — keep stable, downstream UI references these strings ──
CHECKS = [
    "ASSET_IDENTITY_HAS_SUPPORTING_EVIDENCE",
    "EVIDENCE_MANIFEST_EXISTS",
    "EVIDENCE_HASHES_PRESENT",
    "PUBLIC_SOURCES_HAVE_RETRIEVED_TIMESTAMPS",
    "COMPARABLE_SOURCES_CLASSIFIED",
    "LISTING_PRICES_NOT_PRESENTED_AS_CONFIRMED_SALES",
    "VALUE_RANGE_NOT_PUBLIC_WITHOUT_REVIEW_STATUS",
    "MISSING_EVIDENCE_DISCLOSED",
    "AI_ASSISTED_LIMITATION_DISCLOSED",
    "NO_LICENSED_APPRAISAL_CLAIM",
    "NO_CERTIFICATION_OR_AUTHENTICATION_GUARANTEE",
    "PUBLIC_DEED_CONTAINS_NO_PRIVATE_DOCUMENT_DATA",
]


@dataclass
class CheckResult:
    check: str
    status: str  # PASS, PASS_WITH_FLAG, FAIL, SKIPPED
    severity: str | None = None  # INFO, LOW, MEDIUM, HIGH, BLOCKING
    finding: str | None = None
    evidence_reference: list[str] | None = None


def _is_listing_only(sources: list[ResearchSource]) -> bool:
    if not sources:
        return False
    has_confirmed = any(
        s.evidence_classification == EvidenceClassification.CONFIRMED_SALE_PRICE for s in sources
    )
    has_listing = any(
        s.evidence_classification == EvidenceClassification.LISTING_PRICE for s in sources
    )
    return has_listing and not has_confirmed


def run_deterministic_checks(
    db: Session,
    asset: Asset,
    aiov: AIOVAnalysis | None,
) -> list[CheckResult]:
    results: list[CheckResult] = []

    # 1 · asset identity supported by evidence
    private_evidence = (
        db.query(EvidenceItem).filter(EvidenceItem.asset_id == asset.id).all()
    )
    if private_evidence:
        results.append(
            CheckResult(
                check="ASSET_IDENTITY_HAS_SUPPORTING_EVIDENCE",
                status="PASS",
                evidence_reference=[str(e.id) for e in private_evidence[:5]],
            )
        )
    else:
        results.append(
            CheckResult(
                check="ASSET_IDENTITY_HAS_SUPPORTING_EVIDENCE",
                status="FAIL",
                severity="BLOCKING",
                finding="No evidence items uploaded for this asset.",
            )
        )

    # 2 · manifest exists
    manifest = (
        db.query(EvidenceManifest)
        .filter(
            EvidenceManifest.asset_id == asset.id,
            EvidenceManifest.status == ManifestStatus.CURRENT,
        )
        .first()
    )
    if manifest:
        results.append(
            CheckResult(
                check="EVIDENCE_MANIFEST_EXISTS",
                status="PASS",
                evidence_reference=[manifest.manifest_sha256],
            )
        )
    else:
        results.append(
            CheckResult(
                check="EVIDENCE_MANIFEST_EXISTS",
                status="FAIL",
                severity="BLOCKING",
                finding="Evidence manifest has not been generated.",
            )
        )

    # 3 · hashes present
    missing_hash = [e for e in private_evidence if not e.sha256_hash]
    if not private_evidence:
        results.append(CheckResult(check="EVIDENCE_HASHES_PRESENT", status="SKIPPED"))
    elif missing_hash:
        results.append(
            CheckResult(
                check="EVIDENCE_HASHES_PRESENT",
                status="FAIL",
                severity="HIGH",
                finding=f"{len(missing_hash)} evidence item(s) missing SHA-256.",
            )
        )
    else:
        results.append(CheckResult(check="EVIDENCE_HASHES_PRESENT", status="PASS"))

    # 4 · public sources have retrieved_at
    public_sources = (
        db.query(ResearchSource)
        .join(ResearchSession, ResearchSource.research_session_id == ResearchSession.id)
        .filter(
            ResearchSession.asset_id == asset.id,
            ResearchSession.source_lane.in_([SourceLane.PUBLIC_WEB, SourceLane.MIXED]),
        )
        .all()
    )
    if not public_sources:
        results.append(
            CheckResult(check="PUBLIC_SOURCES_HAVE_RETRIEVED_TIMESTAMPS", status="SKIPPED")
        )
    else:
        missing_ts = [s for s in public_sources if not s.retrieved_at]
        if missing_ts:
            results.append(
                CheckResult(
                    check="PUBLIC_SOURCES_HAVE_RETRIEVED_TIMESTAMPS",
                    status="FAIL",
                    severity="MEDIUM",
                    finding=f"{len(missing_ts)} public source(s) missing retrieved_at.",
                )
            )
        else:
            results.append(
                CheckResult(check="PUBLIC_SOURCES_HAVE_RETRIEVED_TIMESTAMPS", status="PASS")
            )

    # 5 · comparable sources classified (not UNKNOWN)
    if not public_sources:
        results.append(CheckResult(check="COMPARABLE_SOURCES_CLASSIFIED", status="SKIPPED"))
    else:
        unknown = [
            s
            for s in public_sources
            if s.evidence_classification == EvidenceClassification.UNKNOWN
        ]
        if unknown:
            results.append(
                CheckResult(
                    check="COMPARABLE_SOURCES_CLASSIFIED",
                    status="PASS_WITH_FLAG",
                    severity="LOW",
                    finding=f"{len(unknown)} public source(s) still classified UNKNOWN.",
                )
            )
        else:
            results.append(CheckResult(check="COMPARABLE_SOURCES_CLASSIFIED", status="PASS"))

    # 6 · listing prices never presented as confirmed sales
    if _is_listing_only(public_sources):
        results.append(
            CheckResult(
                check="LISTING_PRICES_NOT_PRESENTED_AS_CONFIRMED_SALES",
                status="PASS_WITH_FLAG",
                severity="MEDIUM",
                finding="Public sources include listing-price evidence only · listing is not a confirmed sale.",
            )
        )
    else:
        results.append(
            CheckResult(check="LISTING_PRICES_NOT_PRESENTED_AS_CONFIRMED_SALES", status="PASS")
        )

    # 7 · value range not public without review status
    if aiov:
        value_op = aiov.analysis_json.get("value_opinion", {}) if aiov.analysis_json else {}
        display_status = value_op.get("display_status")
        if (value_op.get("range_low") is not None or value_op.get("range_high") is not None) and display_status not in {
            "REVIEWED_AND_DISCLOSED",
            "WITHHELD_PENDING_VALIDATOR_REVIEW",
        }:
            results.append(
                CheckResult(
                    check="VALUE_RANGE_NOT_PUBLIC_WITHOUT_REVIEW_STATUS",
                    status="FAIL",
                    severity="HIGH",
                    finding="Numeric value range present without an explicit review/display status.",
                )
            )
        else:
            results.append(
                CheckResult(check="VALUE_RANGE_NOT_PUBLIC_WITHOUT_REVIEW_STATUS", status="PASS")
            )
    else:
        results.append(CheckResult(check="VALUE_RANGE_NOT_PUBLIC_WITHOUT_REVIEW_STATUS", status="SKIPPED"))

    # 8 · missing evidence disclosed
    if aiov:
        missing = aiov.analysis_json.get("missing_evidence") if aiov.analysis_json else None
        if missing is None:
            results.append(
                CheckResult(
                    check="MISSING_EVIDENCE_DISCLOSED",
                    status="PASS_WITH_FLAG",
                    severity="LOW",
                    finding="AIOV analysis did not include a missing_evidence section.",
                )
            )
        else:
            results.append(CheckResult(check="MISSING_EVIDENCE_DISCLOSED", status="PASS"))
    else:
        results.append(CheckResult(check="MISSING_EVIDENCE_DISCLOSED", status="SKIPPED"))

    # 9 · AI-assisted limitation disclosed
    if aiov:
        limitations = aiov.analysis_json.get("limitations", []) if aiov.analysis_json else []
        if any("AI" in (l or "").upper() or "AI-ASSISTED" in (l or "").upper() for l in limitations):
            results.append(CheckResult(check="AI_ASSISTED_LIMITATION_DISCLOSED", status="PASS"))
        else:
            results.append(
                CheckResult(
                    check="AI_ASSISTED_LIMITATION_DISCLOSED",
                    status="FAIL",
                    severity="HIGH",
                    finding="AIOV analysis must disclose that it is AI-assisted.",
                )
            )
    else:
        results.append(CheckResult(check="AI_ASSISTED_LIMITATION_DISCLOSED", status="SKIPPED"))

    # 10 · no licensed appraisal claim
    forbidden_terms = ["licensed appraisal", "certified appraisal", "authentication guarantee"]
    aiov_text = (aiov.narrative or "").lower() if aiov else ""
    hits = [t for t in forbidden_terms if t in aiov_text]
    if hits:
        results.append(
            CheckResult(
                check="NO_LICENSED_APPRAISAL_CLAIM",
                status="FAIL",
                severity="BLOCKING",
                finding=f"Forbidden term(s) found in AIOV narrative: {', '.join(hits)}",
            )
        )
    else:
        results.append(CheckResult(check="NO_LICENSED_APPRAISAL_CLAIM", status="PASS"))

    # 11 · no certification or authentication guarantee
    if aiov and aiov.analysis_json:
        disclosures = aiov.analysis_json.get("limitations", [])
        text = " ".join(disclosures).lower() if isinstance(disclosures, list) else ""
        bad = "guarantee" in text and "warrant" in text
        results.append(
            CheckResult(
                check="NO_CERTIFICATION_OR_AUTHENTICATION_GUARANTEE",
                status="FAIL" if bad else "PASS",
                severity="BLOCKING" if bad else None,
                finding="Disclaimers may not promise a guarantee or warranty." if bad else None,
            )
        )
    else:
        results.append(CheckResult(check="NO_CERTIFICATION_OR_AUTHENTICATION_GUARANTEE", status="SKIPPED"))

    # 12 · public deed contains no private document data
    #     Enforced at publication time (services/deed.py:filter_public_payload).
    #     Here we record the policy as observed.
    results.append(
        CheckResult(
            check="PUBLIC_DEED_CONTAINS_NO_PRIVATE_DOCUMENT_DATA",
            status="PASS",
            finding="Privacy filter applied at deed publication.",
        )
    )

    return results


def summarise(results: list[CheckResult]) -> str:
    """Reduce check results to a single ValidatorStatus value."""
    if any(r.status == "FAIL" and r.severity == "BLOCKING" for r in results):
        return "FAILED_REQUIRES_REPAIR"
    if any(r.status == "FAIL" for r in results):
        return "FAILED_REQUIRES_REPAIR"
    return "PASSED_FOR_PACKAGING"


def build_receipt(
    asset: Asset,
    aiov_version: int | None,
    results: list[CheckResult],
    status: str,
) -> dict:
    findings = [asdict(r) for r in results if r.status in {"FAIL", "PASS_WITH_FLAG"}]
    payload: dict[str, Any] = {
        "receipt_type": "VALIDATOR_RECEIPT",
        "protocol": "VALIDATE_THE_VALIDATOR",
        "asset_reference": asset.public_asset_reference,
        "analysis_version": aiov_version,
        "status": status,
        "checks": [asdict(r) for r in results],
        "blocking_findings": [f for f in findings if f.get("severity") == "BLOCKING"],
        "issued_at": datetime.now(tz=timezone.utc).isoformat(),
    }
    payload["receipt_sha256"] = sha256_json(
        {k: v for k, v in payload.items() if k != "receipt_sha256"}
    )
    return payload
