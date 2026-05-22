"""Seed the 7 ITAD partners as OUTREACH_READY · idempotent.

Based on Grok-verified research (2026-05-22):
  · Jawa, SellGPU, GreenTek = Track A (specialist · faster pilot)
  · Alta, exIT, Re-Teck, Iron Mountain = Track B (enterprise · slower)
  · ServerMonkey added as a secondary server-level target

All partners enter as OUTREACH_READY / NOT_CONTACTED / NONE agreement
/ AGREEMENT_REQUIRED rights. They CANNOT contribute observations to
comp sets until they progress through IN_CONVERSATION (per the rule
in comp_foundry.add_partner_transaction_observation).
"""
from __future__ import annotations

import json
import uuid

from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.goods import (
    ItadAgreementStatus,
    ItadContactStatus,
    ItadFeedFormat,
    ItadPartner,
    ItadPartnershipStatus,
    RightsStatus,
)


PARTNERS: list[dict] = [
    {
        "slug": "jawa",
        "company_name": "Jawa",
        "company_url": "https://www.jawa.gg",
        "compute_coverage_summary": (
            "GPU-native marketplace · references anonymized GPU sales data · "
            "Track A specialist / faster pilot target."
        ),
    },
    {
        "slug": "sellgpu",
        "company_name": "SellGPU",
        "company_url": "https://www.sellgpu.com",
        "compute_coverage_summary": (
            "Buys GPUs / CPUs / RAM / SSDs / PCs / server components · "
            "supports bulk ITAD · Track A specialist for high-volume "
            "standalone GPU/component comps and smaller compute sellers."
        ),
    },
    {
        "slug": "greentek-solutions",
        "company_name": "GreenTek Solutions",
        "company_url": "https://www.greenteksolutionsllc.com",
        "compute_coverage_summary": (
            "Advertises buyback for DGX H100/A100, H100, A100, A40, L40, "
            "V100, T4, deep-learning servers, custom GPU rigs, storage "
            "and networking · Track A AI-hardware-specific buyback target."
        ),
    },
    {
        "slug": "alta-technologies",
        "company_name": "Alta Technologies",
        "company_url": "https://www.altatech.com",
        "compute_coverage_summary": (
            "Tested new / used / refurbished NVIDIA H100/H200/A100-class GPUs, "
            "AI servers, full racks · R2v3 certified · Track B enterprise "
            "AI hardware partner target."
        ),
    },
    {
        "slug": "exit-technologies",
        "company_name": "exIT Technologies",
        "company_url": "https://www.exittechnologies.com",
        "compute_coverage_summary": (
            "Buys retired NVIDIA DGX servers, H100/H200, A100/A800, L40S/L40, "
            "V100, DGX/HGX nodes, NVLink/NVSwitch · requests configurations, "
            "photos, pickup details · Track B enterprise · very aligned "
            "with Defendable record architecture."
        ),
    },
    {
        "slug": "re-teck",
        "company_name": "Re-Teck",
        "company_url": "https://www.re-teck.com",
        "compute_coverage_summary": (
            "ITAD services for cloud and AI data centers · GPU-dense servers, "
            "testing, repair, remarketing · Track B enterprise · higher-level "
            "AI data-center / enterprise partner lead."
        ),
    },
    {
        "slug": "iron-mountain",
        "company_name": "Iron Mountain",
        "company_url": "https://www.ironmountain.com",
        "compute_coverage_summary": (
            "Global IT asset lifecycle management and ITAD · secure "
            "disposition, remarketing, resale / value recovery · Track B "
            "enterprise institutional path · likely slower partnership cycle."
        ),
    },
    {
        "slug": "servermonkey",
        "company_name": "ServerMonkey",
        "company_url": "https://www.servermonkey.com",
        "compute_coverage_summary": (
            "Buys back used servers / networking equipment · sells refurbished "
            "GPU servers for AI/ML/HPC workloads · secondary server-level / "
            "configuration comp target."
        ),
    },
]


def _ensure_partner(db: Session, spec: dict) -> ItadPartner:
    existing = db.query(ItadPartner).filter(ItadPartner.slug == spec["slug"]).first()
    if existing:
        return existing
    row = ItadPartner(
        id=uuid.uuid4(),
        slug=spec["slug"],
        company_name=spec["company_name"],
        company_url=spec.get("company_url"),
        compute_coverage_summary=spec["compute_coverage_summary"],
        partnership_status=ItadPartnershipStatus.OUTREACH_READY,
        feed_format=ItadFeedFormat.UNKNOWN,
        agreement_status=ItadAgreementStatus.NONE,
        rights_scope=RightsStatus.AGREEMENT_REQUIRED,
        contact_status=ItadContactStatus.NOT_CONTACTED,
        contact_notes=None,
    )
    db.add(row)
    db.flush()
    return row


def seed_itad_partners() -> dict:
    db: Session = SessionLocal()
    try:
        partners = [_ensure_partner(db, p) for p in PARTNERS]
        db.commit()
        return {
            "partners_seeded": len(partners),
            "slugs": [p.slug for p in partners],
            "partnership_status": "OUTREACH_READY",
            "agreement_status": "NONE",
            "rights_scope": "AGREEMENT_REQUIRED",
        }
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    result = seed_itad_partners()
    print(json.dumps(result, indent=2))
