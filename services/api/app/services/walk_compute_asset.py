"""Parameterized walker · runs any single compute asset through the live
evidence → manifest → AIOV (Kimi) → research (Brave) → validator → deed
pipeline. Replaces the per-asset seed_compute_NNN.py scripts.

Drop in a CompactSpec at the bottom of this file (or via the SPEC env
var pointing at a JSON file) and execute:

    python -m app.services.walk_compute_asset

Idempotent: if a public deed already exists for the asset_reference,
the script returns the existing slug instead of issuing a duplicate.
"""
from __future__ import annotations

import json
import os
import sys
import uuid
from dataclasses import dataclass, field
from typing import Optional

from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.integrations import brave_llm_context
from app.integrations.model_gateway import get_model_gateway
from app.models.ai import AIOVAnalysis, AIOVStatus, WorkflowType
from app.models.asset import (
    Asset,
    AssetClass,
    AssetStatus,
    ComputeAssetProfile,
    ConditionStatus,
    IntendedUse,
)
from app.models.deed import DefendableDeed
from app.models.evidence import (
    EvidenceItem,
    EvidenceType,
    IngestionStatus,
    Visibility,
)
from app.models.organization import Organization
from app.models.user import User
from app.models.validator import ValidatorReview, ValidatorStatus
from app.services.deed import create_deed, publish_public
from app.services.hashing import sha256_bytes
from app.services.manifest import regenerate_manifest
from app.services.validator_checks import (
    build_receipt,
    run_deterministic_checks,
    summarise,
)


@dataclass
class ComputeAssetSpec:
    asset_reference: str        # "DOV-COMPUTE-000003"
    name: str                   # "RTX 3090 Founders Edition · Mint"
    description: str
    manufacturer: str           # "NVIDIA"
    model: str                  # "GeForce RTX 3090 Founders Edition"
    architecture: str           # "Ampere (GA102)"
    vram_gb: int
    memory_type: str            # "GDDR6X"
    memory_bus_width_bits: int  # 384
    condition: str              # "NEW" "EXCELLENT" "GOOD" "FAIR"
    intended_use: str           # IntendedUse enum value
    host_rig: str               # "Threadripper 9970X · TRX50-SAGE Pro WS"
    driver_version: str
    cuda_version: str
    benchmark_workload: str
    research_query: str         # Brave LLM Context query for market sources
    market_sources_n: int = 5
    # ── Operator-asking-price · doctrine: claim only, not validation ──
    operator_ask_price_usd: int | None = None
    operator_ask_currency: str = "USD"
    extra_evidence_fields: dict = field(default_factory=dict)


def _build_value_opinion(spec: ComputeAssetSpec) -> dict:
    """Compose the AIOV value_opinion block.

    Two states today:
      · OPERATOR_ASK_PRICE · operator has stated an asking price ·
        deed publicly shows the price labeled as operator claim
      · WITHHELD_PENDING_VALIDATOR_REVIEW · default · no public value

    Future: REVIEWED_AND_DISCLOSED for confirmed-sale-backed validated
    ranges (gated on eBay Marketplace Insights or confirmed sale receipts).
    """
    if spec.operator_ask_price_usd and spec.operator_ask_price_usd > 0:
        return {
            "display_status": "OPERATOR_ASK_PRICE",
            "operator_ask_price_usd": int(spec.operator_ask_price_usd),
            "operator_ask_currency": spec.operator_ask_currency,
            "currency": spec.operator_ask_currency,
            "range_low": None,
            "range_high": None,
            "notes": (
                "Operator's stated asking price. Operator claim only · "
                "not a validator-issued value, professional appraisal, or "
                "confirmed-sale comparable. A public value range backed by "
                "confirmed-sale evidence may be added after validator review."
            ),
        }
    return {
        "display_status": "WITHHELD_PENDING_VALIDATOR_REVIEW",
        "currency": "USD",
        "range_low": None,
        "range_high": None,
        "notes": (
            "Public value range may be added only after evidence and "
            "confirmed-sale comparable review."
        ),
    }


def _benchmark_payload(spec: ComputeAssetSpec) -> dict:
    return {
        "evidence_type": "BENCHMARK_OUTPUT",
        "asset_reference": spec.asset_reference,
        "manufacturer": spec.manufacturer,
        "model": spec.model,
        "architecture": spec.architecture,
        "vram_gb": spec.vram_gb,
        "memory_type": spec.memory_type,
        "memory_bus_width_bits": spec.memory_bus_width_bits,
        "condition": spec.condition,
        "host_rig": spec.host_rig,
        "driver_version": spec.driver_version,
        "cuda_version": spec.cuda_version,
        "benchmark": {
            "name": "ILLUSTRATIVE_INFERENCE_THROUGHPUT",
            "workload": spec.benchmark_workload,
            "tokens_per_second": "<illustrative>",
            "peak_vram_gb": "<illustrative>",
        },
        "captured_at": "2026-05-22T22:00:00Z",
        "captured_by": "defendable-box · box-01.swarmbee.defendable.eth",
        **spec.extra_evidence_fields,
    }


def _get_demo_user_org(db: Session) -> tuple[User, Organization]:
    user = db.query(User).filter(User.email.like("%swarmandbee.ai")).first()
    if not user:
        raise RuntimeError("Seed user not found · run base seed first.")
    org = db.query(Organization).filter(Organization.slug == "swarmbee").first()
    if not org:
        raise RuntimeError("Demo org not found · run base seed first.")
    return user, org


def _ensure_asset(db: Session, org: Organization, user: User, spec: ComputeAssetSpec) -> Asset:
    asset = (
        db.query(Asset)
        .filter(
            Asset.organization_id == org.id,
            Asset.public_asset_reference == spec.asset_reference,
        )
        .first()
    )
    if asset:
        return asset
    asset = Asset(
        id=uuid.uuid4(),
        organization_id=org.id,
        public_asset_reference=spec.asset_reference,
        asset_class=AssetClass.COMPUTE_HARDWARE,
        category="GPU_ACCELERATOR",
        name=spec.name,
        description=spec.description,
        status=AssetStatus.EVIDENCE_INTAKE,
        client_internal_reference=f"DEMO-{spec.asset_reference}",
        created_by=user.id,
    )
    db.add(asset)
    db.flush()
    db.add(
        ComputeAssetProfile(
            id=uuid.uuid4(),
            asset_id=asset.id,
            manufacturer=spec.manufacturer,
            model=spec.model,
            gpu_count=1,
            vram_per_gpu_gb=spec.vram_gb,
            cpu="AMD Ryzen Threadripper 9970X",
            ram_gb=128,
            operating_system="Ubuntu 24.04 LTS",
            condition_status=ConditionStatus(spec.condition),
            operational_status="OPERATIONAL",
            intended_use=IntendedUse(spec.intended_use),
        )
    )
    return asset


def _ensure_evidence(db: Session, asset: Asset, user: User, spec: ComputeAssetSpec) -> EvidenceItem:
    body = json.dumps(_benchmark_payload(spec), indent=2, sort_keys=True).encode("utf-8")
    digest = sha256_bytes(body)
    existing = (
        db.query(EvidenceItem)
        .filter(EvidenceItem.asset_id == asset.id)
        .filter(EvidenceItem.sha256_hash == digest)
        .first()
    )
    if existing:
        return existing
    safe_ref = spec.asset_reference.lower().replace("-", "_")
    evidence = EvidenceItem(
        id=uuid.uuid4(),
        organization_id=asset.organization_id,
        asset_id=asset.id,
        filename=f"{safe_ref}_benchmark.json",
        storage_key=(
            f"organizations/{asset.organization_id}/assets/{asset.id}"
            f"/raw/{safe_ref}_benchmark.json"
        ),
        content_type="application/json",
        byte_size=len(body),
        evidence_type=EvidenceType.BENCHMARK_OUTPUT,
        visibility=Visibility.PRIVATE,
        ingestion_status=IngestionStatus.INDEXED,
        sha256_hash=digest,
        uploaded_by=user.id,
        provenance="USER_UPLOAD",
    )
    db.add(evidence)
    db.flush()
    return evidence


def _live_brave_research(query: str, max_sources: int) -> list[dict]:
    result = brave_llm_context.search(
        query=query,
        maximum_number_of_urls=max_sources,
        maximum_number_of_tokens=2048,
    )
    if result.status != "COMPLETED":
        print(f"  [brave] {result.status}: {result.error}")
        return []
    out = []
    for s in result.sources:
        out.append(
            {
                "source_id": f"BRAVE-{uuid.uuid4().hex[:8]}",
                "source_type": "PUBLIC_RESEARCH",
                "url": s.url,
                "title": s.title,
                "domain": s.domain,
                "supports": "MARKET_CONTEXT",
                "evidence_classification": "LISTING_PRICE_OR_MARKET_COMMENTARY",
                "ai_assisted_inclusion": True,
                "warning": (
                    "Per doctrine, a public listing is not a confirmed sale. "
                    "Validator review required before any value claim."
                ),
            }
        )
    return out


def _live_kimi_aiov(
    asset: Asset,
    evidence: EvidenceItem,
    spec: ComputeAssetSpec,
    market_sources: list[dict],
) -> tuple[str, Optional[dict]]:
    gateway = get_model_gateway()
    prompt_payload = {
        "asset": {
            "reference": asset.public_asset_reference,
            "name": asset.name,
            "asset_class": asset.asset_class.value,
            "category": asset.category,
            "description": asset.description,
            "compute_profile": {
                "manufacturer": spec.manufacturer,
                "model": spec.model,
                "architecture": spec.architecture,
                "vram_gb": spec.vram_gb,
                "memory_type": spec.memory_type,
                "condition": spec.condition,
            },
        },
        "evidence_items": [
            {
                "source_id": str(evidence.id),
                "evidence_type": evidence.evidence_type.value,
                "filename": evidence.filename,
                "sha256": evidence.sha256_hash,
                "summary": (
                    f"Benchmark receipt for {spec.model}. Captures inference "
                    f"throughput context. Tokens-per-second and peak VRAM "
                    f"remain illustrative pending operator confirmation."
                ),
            }
        ],
        "market_sources": market_sources,
        "required_output": {
            "narrative_style": (
                "Concise, evidence-aware, draft language. Cite source_id for "
                "every claim. List missing evidence. Include standard "
                "limitations. Aim for ~600-1200 chars of plain prose · no "
                "JSON code blocks · no headings."
            ),
            "must_include_limitations": [
                "AI-assisted draft only",
                "Not a licensed appraisal",
                "Not a warranty, certification, or authentication guarantee",
            ],
            "value_opinion": {
                "display_status": "WITHHELD_PENDING_VALIDATOR_REVIEW",
                "may_state_range_publicly": False,
            },
        },
    }
    result = gateway.generate_structured(
        workflow_type=WorkflowType.AIOV_DRAFT,
        prompt_version="aiov_draft.v1",
        input_reference={"asset_id": str(asset.id), "evidence_id": str(evidence.id)},
        prompt_payload=prompt_payload,
        thinking_enabled=False,
    )
    if result.status != "GENERATED":
        raise RuntimeError(
            f"AIOV generation failed · status={result.status} · error={result.error}"
        )
    narrative = (result.output_text or "").strip()
    if not narrative:
        raise RuntimeError("Kimi returned empty narrative.")
    if len(narrative) > 1800:
        narrative = narrative[:1800].rstrip() + " […]"
    return narrative, result.output_json


def walk(spec: ComputeAssetSpec, force_new_version: bool = False) -> dict:
    db: Session = SessionLocal()
    try:
        user, org = _get_demo_user_org(db)
        asset = _ensure_asset(db, org, user, spec)

        if not force_new_version:
            existing_deed = (
                db.query(DefendableDeed)
                .filter(DefendableDeed.asset_id == asset.id)
                .filter(DefendableDeed.is_public == True)  # noqa: E712
                .order_by(DefendableDeed.version.desc())
                .first()
            )
            if existing_deed:
                return {
                    "asset_reference": asset.public_asset_reference,
                    "deed_reference": existing_deed.deed_reference,
                    "public_slug": existing_deed.public_slug,
                    "record_hash": existing_deed.record_hash,
                    "status": existing_deed.status.value,
                    "already_existed": True,
                }

        evidence = _ensure_evidence(db, asset, user, spec)
        print(f"  evidence indexed · sha256={evidence.sha256_hash[:16]}…")

        manifest = regenerate_manifest(db, asset)
        print(f"  manifest regenerated · sha256={manifest.manifest_sha256[:16]}…")

        print(f"  calling Brave for: {spec.research_query!r}")
        market_sources = _live_brave_research(spec.research_query, spec.market_sources_n)
        print(f"  Brave returned {len(market_sources)} sources")

        print("  calling Kimi for AIOV draft …")
        narrative, output_json = _live_kimi_aiov(asset, evidence, spec, market_sources)
        print(f"  Kimi narrative · {len(narrative)} chars")

        # Determine the next AIOV version · prevents tie at version=1 when
        # an earlier walker run already left an AIOV row on this asset.
        prev_aiov_version = (
            db.query(AIOVAnalysis)
            .filter(AIOVAnalysis.asset_id == asset.id)
            .order_by(AIOVAnalysis.version.desc())
            .first()
        )
        next_aiov_version = (prev_aiov_version.version + 1) if prev_aiov_version else 1

        aiov_payload = {
            "analysis_type": "AI_ASSISTED_OPINION_OF_VALUE",
            "asset_reference": asset.public_asset_reference,
            "asset_class": asset.asset_class.value,
            "status": "GENERATED_FOR_VALIDATOR_REVIEW",
            "intelligence_engine": "kimi-k2.6 · live",
            "prompt_version": "aiov_draft.v1",
            "identity_summary": {
                "manufacturer": spec.manufacturer,
                "model": spec.model,
                "condition": spec.condition,
                "configuration_confidence": "SUPPORTED_BY_SUBMITTED_EVIDENCE",
            },
            "evidence_basis": [
                {
                    "source_id": str(evidence.id),
                    "source_type": "PRIVATE_EVIDENCE",
                    "evidence_type": "BENCHMARK_OUTPUT",
                    "supports": "ASSET_CONTEXT",
                    "sha256": evidence.sha256_hash,
                }
            ],
            "market_evidence": market_sources,
            "value_opinion": _build_value_opinion(spec),
            "missing_evidence": ["PURCHASE_RECEIPT", "CONFIRMED_SALE_COMPARABLES"],
            "limitations": [
                "AI-assisted draft only",
                "Not a licensed appraisal",
                "Not a warranty, certification, or authentication guarantee",
            ],
            "kimi_output_json_keys": (
                list(output_json.keys()) if isinstance(output_json, dict) else []
            ),
        }
        aiov = AIOVAnalysis(
            id=uuid.uuid4(),
            asset_id=asset.id,
            version=next_aiov_version,
            status=AIOVStatus.GENERATED_FOR_VALIDATOR_REVIEW,
            analysis_json=aiov_payload,
            narrative=narrative,
            supporting_source_ids=[str(evidence.id)],
            missing_evidence_json={
                "missing_evidence_types": aiov_payload["missing_evidence"],
            },
        )
        db.add(aiov)
        db.flush()

        results = run_deterministic_checks(db, asset, aiov)
        status_value = summarise(results)
        receipt = build_receipt(asset, aiov.version, results, status_value)
        review = ValidatorReview(
            id=uuid.uuid4(),
            asset_id=asset.id,
            aiov_analysis_id=aiov.id,
            version=next_aiov_version,
            status=ValidatorStatus(status_value),
            protocol="VALIDATE_THE_VALIDATOR",
            findings_json=receipt.get("blocking_findings", []),
            checks_json=receipt["checks"],
            receipt_sha256=receipt["receipt_sha256"],
            reviewed_by=user.id,
        )
        db.add(review)
        db.flush()
        print(f"  validator: {status_value}")

        if status_value != "PASSED_FOR_PACKAGING":
            db.commit()
            return {
                "asset_reference": asset.public_asset_reference,
                "deed_reference": None,
                "public_slug": None,
                "record_hash": None,
                "validator_status": status_value,
                "blocking_findings": receipt.get("blocking_findings", []),
                "already_existed": False,
            }

        deed = create_deed(db, asset, issued_by_user_id=user.id)
        publish_public(deed)
        db.commit()
        return {
            "asset_reference": asset.public_asset_reference,
            "deed_reference": deed.deed_reference,
            "public_slug": deed.public_slug,
            "record_hash": deed.record_hash,
            "validator_status": status_value,
            "narrative_length": len(narrative),
            "narrative_preview": narrative[:300] + ("…" if len(narrative) > 300 else ""),
            "brave_sources": len(market_sources),
            "already_existed": False,
        }
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# ── Pre-defined specs · pick one with the SPEC env var ──────────────
SPECS: dict[str, ComputeAssetSpec] = {
    "rtx_pro_6000_blackwell": ComputeAssetSpec(
        asset_reference="DOV-COMPUTE-000001",
        name="RTX PRO 6000 Blackwell Workstation GPU",
        description=(
            "NVIDIA RTX PRO 6000 Blackwell workstation GPU · 96 GB ECC "
            "GDDR7 · Tier 1 Cook card in the Swarm & Bee fleet (4-per-case "
            "WRX90 Threadripper PRO rigs · 384 GB combined VRAM · trains "
            "70B+ models). Operator-owned single unit available."
        ),
        manufacturer="NVIDIA",
        model="RTX PRO 6000 Blackwell",
        architecture="Blackwell (workstation)",
        vram_gb=96,
        memory_type="ECC GDDR7",
        memory_bus_width_bits=512,
        condition="NEW",
        intended_use="TRAINING",
        host_rig="WRX90 Threadripper PRO · server chassis",
        driver_version="555.42.06",
        cuda_version="12.5",
        benchmark_workload="Qwen-70B FP8 · batch 1 · 8192 ctx",
        research_query="NVIDIA RTX PRO 6000 Blackwell 96GB workstation price 2026",
        market_sources_n=6,
        operator_ask_price_usd=9850,
    ),
    "rtx5090_rog_astral": ComputeAssetSpec(
        asset_reference="DOV-COMPUTE-000002",
        name="RTX 5090 ROG ASTRAL O32G · Tier 2 Serve",
        description=(
            "NVIDIA GeForce RTX 5090 ROG ASTRAL O32G · Blackwell consumer "
            "architecture · 32 GB GDDR7 · Tier 2 Serve card in the Swarm "
            "& Bee fleet."
        ),
        manufacturer="NVIDIA",
        model="GeForce RTX 5090 ROG ASTRAL O32G",
        architecture="Blackwell (GB202)",
        vram_gb=32,
        memory_type="GDDR7",
        memory_bus_width_bits=512,
        condition="NEW",
        intended_use="INFERENCE",
        host_rig="Threadripper 9970X · TRX50-SAGE Pro WS · 128 GB DDR5 ECC",
        driver_version="555.42.06",
        cuda_version="12.6",
        benchmark_workload="Qwen-9B-FP8 · batch 4 · 4096 ctx",
        research_query="NVIDIA RTX 5090 ROG ASTRAL 32GB price 2026",
        market_sources_n=5,
        operator_ask_price_usd=3900,
    ),
    "rtx3090_founders_mint": ComputeAssetSpec(
        asset_reference="DOV-COMPUTE-000003",
        name="RTX 3090 Founders Edition · 24 GB · Mint",
        description=(
            "NVIDIA GeForce RTX 3090 Founders Edition · Ampere "
            "architecture · 24 GB GDDR6X · operator-owned mint-condition "
            "single unit · suitable for 13B-30B inference and FLUX.1 "
            "image generation."
        ),
        manufacturer="NVIDIA",
        model="GeForce RTX 3090 Founders Edition",
        architecture="Ampere (GA102)",
        vram_gb=24,
        memory_type="GDDR6X",
        memory_bus_width_bits=384,
        condition="NEW",  # "mint" maps cleanest to NEW in ConditionStatus
        intended_use="INFERENCE",
        host_rig="Operator workstation · PCIe 4.0 x16",
        driver_version="555.42.06",
        cuda_version="12.6",
        benchmark_workload="Llama-3-13B-Q5 · batch 1 · 8192 ctx",
        research_query="NVIDIA RTX 3090 Founders Edition 24GB used price 2026",
        market_sources_n=6,
        operator_ask_price_usd=950,
        extra_evidence_fields={
            "condition_notes": (
                "Operator-owned single unit. Reported mint condition. "
                "Original Founders Edition reference cooler. Operator "
                "attestation only · no third-party inspection on file."
            ),
            "tdp_watts": 350,
            "power_connector": "12VHPWR (NVL Cable)",
        },
    ),
}


def _walk_all_with_prices() -> dict:
    """Re-walk all three live deeds as v2 with operator-asking prices."""
    out = {}
    for key in ("rtx_pro_6000_blackwell", "rtx5090_rog_astral", "rtx3090_founders_mint"):
        print(f"\n══ walking {key} ══")
        out[key] = walk(SPECS[key], force_new_version=True)
        print(json.dumps(out[key], indent=2, default=str))
    return out


if __name__ == "__main__":
    spec_key = os.environ.get("SPEC", "rtx5090_rog_astral")
    force = os.environ.get("FORCE_NEW", "false").lower() in {"1", "true", "yes"}
    if spec_key == "all":
        _walk_all_with_prices()
        sys.exit(0)
    if spec_key not in SPECS:
        print(f"Unknown SPEC={spec_key!r} · choose from: {list(SPECS.keys())} or 'all'")
        sys.exit(1)
    spec = SPECS[spec_key]
    print(f"═══ walking {spec.asset_reference} · {spec.name} (force_new={force}) ═══")
    result = walk(spec, force_new_version=force)
    print("\n═══ result ═══")
    print(json.dumps(result, indent=2, default=str))
