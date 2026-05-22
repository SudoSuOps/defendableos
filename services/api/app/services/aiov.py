"""AIOV draft generation · evidence-aware, validator-aware, never a final number."""
from __future__ import annotations

import uuid
from typing import Iterable

from sqlalchemy.orm import Session

from app.integrations.model_gateway import get_model_gateway
from app.models.ai import (
    AIOutput,
    AIOutputStatus,
    AIOVAnalysis,
    AIOVStatus,
    WorkflowType,
)
from app.models.asset import Asset
from app.models.evidence import EvidenceItem
from app.models.research import ResearchSource
from app.services.hashing import sha256_json


def _build_input_reference(asset: Asset, evidence_ids: list[str], source_ids: list[str]) -> dict:
    return {
        "asset_reference": asset.public_asset_reference,
        "asset_class": asset.asset_class.value,
        "evidence_ids": evidence_ids,
        "research_source_ids": source_ids,
    }


def _scaffold_analysis(
    asset: Asset,
    evidence_items: list[EvidenceItem],
    sources: list[ResearchSource],
    narrative: str,
) -> dict:
    profile = asset.compute_profile
    return {
        "analysis_type": "AI_ASSISTED_OPINION_OF_VALUE",
        "asset_reference": asset.public_asset_reference,
        "asset_class": asset.asset_class.value,
        "status": "GENERATED_FOR_VALIDATOR_REVIEW",
        "identity_summary": {
            "manufacturer": profile.manufacturer if profile else None,
            "model": profile.model if profile else None,
            "configuration_confidence": (
                "SUPPORTED_BY_SUBMITTED_EVIDENCE"
                if evidence_items
                else "NOT_YET_SUPPORTED"
            ),
        },
        "evidence_basis": [
            {
                "source_id": str(e.id),
                "source_type": "PRIVATE_EVIDENCE",
                "evidence_type": e.evidence_type.value,
                "supports": "ASSET_IDENTITY"
                if e.evidence_type.value in {"PRODUCT_SPECIFICATION", "SERIAL_OR_PHOTO"}
                else "ASSET_CONTEXT",
                "sha256": e.sha256_hash,
            }
            for e in evidence_items
        ],
        "market_evidence": [
            {
                "source_id": str(s.id),
                "classification": s.evidence_classification.value,
                "url": s.source_url,
                "publisher": s.publisher_domain,
                "relevance": "REVIEW_REQUIRED",
                "limitations": (
                    ["Listing price is not confirmed sale price"]
                    if s.evidence_classification.value == "LISTING_PRICE"
                    else []
                ),
            }
            for s in sources
        ],
        "value_opinion": {
            "display_status": "WITHHELD_PENDING_VALIDATOR_REVIEW",
            "currency": "USD",
            "range_low": None,
            "range_high": None,
            "notes": "A public value range may be added only after evidence and comparable review.",
        },
        "missing_evidence": _infer_missing(evidence_items, sources),
        "limitations": [
            "AI-assisted draft only",
            "Not a licensed appraisal",
            "Not a warranty, certification, or authentication guarantee",
        ],
        "narrative": narrative,
    }


def _infer_missing(evidence: Iterable[EvidenceItem], sources: Iterable[ResearchSource]) -> list[str]:
    missing: list[str] = []
    have_types = {e.evidence_type.value for e in evidence}
    if "BENCHMARK_OUTPUT" not in have_types:
        missing.append("BENCHMARK_OUTPUT")
    if "PURCHASE_RECEIPT" not in have_types:
        missing.append("PURCHASE_RECEIPT")
    if not any(
        s.evidence_classification.value == "CONFIRMED_SALE_PRICE" for s in sources
    ):
        missing.append("CONFIRMED_SALE_COMPARABLES")
    return missing


def generate_aiov(
    db: Session,
    asset: Asset,
    included_evidence_item_ids: list[uuid.UUID] | None,
    included_research_source_ids: list[uuid.UUID] | None,
    notes: str,
) -> AIOVAnalysis:
    # Resolve evidence + sources within asset's scope.
    ev_q = db.query(EvidenceItem).filter(EvidenceItem.asset_id == asset.id)
    if included_evidence_item_ids:
        ev_q = ev_q.filter(EvidenceItem.id.in_(included_evidence_item_ids))
    evidence_items = list(ev_q)

    src_q = (
        db.query(ResearchSource)
        .join(ResearchSource.session)
        .filter(ResearchSource.session.has(asset_id=asset.id))
    )
    if included_research_source_ids:
        src_q = src_q.filter(ResearchSource.id.in_(included_research_source_ids))
    sources = list(src_q)

    # Call the model gateway. Falls back to a structured local scaffold when
    # the provider is not configured · still produces a usable AIOV draft.
    gateway = get_model_gateway()
    evidence_summary = [
        {
            "id": str(e.id),
            "type": e.evidence_type.value,
            "filename": e.filename,
            "sha256": e.sha256_hash,
        }
        for e in evidence_items
    ]
    source_summary = [
        {
            "id": str(s.id),
            "classification": s.evidence_classification.value,
            "title": s.title,
            "domain": s.publisher_domain,
            "url": s.source_url,
            "retrieved_at": s.retrieved_at.isoformat() if s.retrieved_at else None,
        }
        for s in sources
    ]

    gateway_result = gateway.generate_structured(
        workflow_type=WorkflowType.AIOV_DRAFT,
        prompt_version="aiov_compute_v1",
        input_reference=_build_input_reference(
            asset,
            [str(e.id) for e in evidence_items],
            [str(s.id) for s in sources],
        ),
        prompt_payload={
            "asset": {
                "reference": asset.public_asset_reference,
                "class": asset.asset_class.value,
                "category": asset.category,
                "name": asset.name,
                "description": asset.description,
                "manufacturer": asset.compute_profile.manufacturer if asset.compute_profile else None,
                "model": asset.compute_profile.model if asset.compute_profile else None,
            },
            "evidence_items": evidence_summary,
            "research_sources": source_summary,
            "operator_notes": notes,
        },
        thinking_enabled=False,
    )

    narrative = (
        gateway_result.output_text
        or "AI-assisted AIOV draft generated locally without an external model. "
        "Sources are listed in evidence_basis and market_evidence. A reviewer "
        "must run Validate the Validator before any value range is published."
    )

    analysis_payload = _scaffold_analysis(asset, evidence_items, sources, narrative)
    # If the gateway produced structured output, merge non-conflicting keys.
    if gateway_result.output_json:
        for key in ("missing_evidence", "limitations"):
            if key in gateway_result.output_json and isinstance(
                gateway_result.output_json[key], list
            ):
                analysis_payload[key] = gateway_result.output_json[key]

    analysis_hash = sha256_json(analysis_payload)
    ai_output = AIOutput(
        id=uuid.uuid4(),
        organization_id=asset.organization_id,
        asset_id=asset.id,
        workflow_type=WorkflowType.AIOV_DRAFT,
        model_provider=gateway_result.provider,
        model_name=gateway_result.model,
        prompt_version="aiov_compute_v1",
        input_reference_json=_build_input_reference(
            asset,
            [str(e.id) for e in evidence_items],
            [str(s.id) for s in sources],
        ),
        output_text=narrative,
        output_json=analysis_payload,
        output_sha256=analysis_hash,
        status=AIOutputStatus.GENERATED
        if gateway_result.status == "GENERATED"
        else AIOutputStatus.NOT_CONFIGURED,
        thinking_enabled=False,
        error_message=gateway_result.error,
    )
    db.add(ai_output)
    db.flush()

    # Supersede prior analyses.
    db.query(AIOVAnalysis).filter(
        AIOVAnalysis.asset_id == asset.id,
        AIOVAnalysis.status != AIOVStatus.SUPERSEDED,
    ).update({"status": AIOVStatus.SUPERSEDED})

    latest = (
        db.query(AIOVAnalysis)
        .filter(AIOVAnalysis.asset_id == asset.id)
        .order_by(AIOVAnalysis.version.desc())
        .first()
    )
    next_version = (latest.version + 1) if latest else 1
    analysis = AIOVAnalysis(
        id=uuid.uuid4(),
        asset_id=asset.id,
        version=next_version,
        status=AIOVStatus.GENERATED_FOR_VALIDATOR_REVIEW,
        analysis_json=analysis_payload,
        narrative=narrative,
        supporting_source_ids=[str(s.id) for s in sources],
        missing_evidence_json={"missing_evidence_types": analysis_payload["missing_evidence"]},
        generated_by_output_id=ai_output.id,
    )
    db.add(analysis)
    db.flush()
    return analysis
