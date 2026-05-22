"""Seed Swarm & Bee Demo · the founder-demo organization.

Idempotent. Safe to run multiple times. Creates:
  - demo user + ORG_ADMIN membership
  - Swarm & Bee Demo organization
  - swarmbee.defendable.eth reservation (mock, RESERVED_NOT_ISSUED)
  - RTX PRO 6000 Blackwell asset · DOV-COMPUTE-000001
  - Defendable Box 01 edge node + box-01.swarmbee.defendable.eth reservation
  - A full proof chain: evidence item → manifest → AIOV draft →
    validator review → published DRAFT deed
  - So /verify/{slug} · /showcase/{slug} · /ledger lookup all resolve
    against this asset out of the box on first deploy
"""
from __future__ import annotations

import json
import uuid

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.ai import AIOVAnalysis, AIOVStatus
from app.models.asset import (
    Asset,
    AssetClass,
    AssetStatus,
    ComputeAssetProfile,
    ConditionStatus,
    IntendedUse,
)
from app.models.deed import DefendableDeed
from app.models.edge import EdgeNode, EnrollmentStatus
from app.models.ens import (
    ENSIdentity,
    IdentityStatus,
    IdentityType,
    IssuanceMode,
)
from app.models.evidence import (
    EvidenceItem,
    EvidenceType,
    IngestionStatus,
    Visibility,
)
from app.models.organization import (
    ENSStatus,
    Organization,
    OrganizationMembership,
    OrgRole,
)
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


DEMO_ORG_SLUG = "swarmbee"
DEMO_ORG_NAME = "Swarm & Bee Demo"

# Canonical illustrative benchmark payload · the same shape we ship in
# data/sample-evidence/sample_benchmark.json so the demo evidence is
# consistent across local dev and production seed.
_SAMPLE_BENCHMARK = {
    "evidence_type": "BENCHMARK_OUTPUT",
    "asset_reference": "DOV-COMPUTE-000001",
    "model": "RTX PRO 6000 Blackwell Workstation GPU",
    "driver_version": "555.42.06",
    "cuda_version": "12.5",
    "benchmark": {
        "name": "ILLUSTRATIVE_LLM_THROUGHPUT",
        "workload": "Qwen-7B FP16 · batch 1 · 4096 ctx",
        "tokens_per_second": "<illustrative>",
        "peak_vram_gb": "<illustrative>",
    },
    "captured_at": "2026-05-22T12:00:00Z",
    "captured_by": "defendable-box · box-01.swarmbee.defendable.eth",
}


def _get_or_create_user(db: Session) -> User:
    user = db.query(User).filter(User.email == settings.demo_user_email).first()
    if user:
        return user
    user = User(
        id=uuid.uuid4(),
        email=settings.demo_user_email,
        name="Demo Operator",
        hashed_password=hash_password(settings.demo_user_password),
        is_platform_admin=True,  # demo operator can publish + admin
    )
    db.add(user)
    db.flush()
    return user


def _get_or_create_org(db: Session) -> Organization:
    org = db.query(Organization).filter(Organization.slug == DEMO_ORG_SLUG).first()
    if org:
        return org
    org = Organization(
        id=uuid.uuid4(),
        name=DEMO_ORG_NAME,
        slug=DEMO_ORG_SLUG,
        ens_label="swarmbee",
        ens_name=f"swarmbee.{settings.ens_parent_name}",
        ens_status=ENSStatus.RESERVED_NOT_ISSUED,
    )
    db.add(org)
    db.flush()
    return org


def _ensure_membership(db: Session, org: Organization, user: User) -> None:
    exists = (
        db.query(OrganizationMembership)
        .filter(
            OrganizationMembership.organization_id == org.id,
            OrganizationMembership.user_id == user.id,
        )
        .first()
    )
    if exists:
        return
    db.add(
        OrganizationMembership(
            id=uuid.uuid4(),
            organization_id=org.id,
            user_id=user.id,
            role=OrgRole.ORG_ADMIN,
        )
    )


def _ensure_ens(
    db: Session,
    *,
    org_id: uuid.UUID,
    ens_name: str,
    label: str,
    identity_type: IdentityType,
    asset_id: uuid.UUID | None = None,
    edge_node_id: uuid.UUID | None = None,
) -> ENSIdentity:
    existing = db.query(ENSIdentity).filter(ENSIdentity.ens_name == ens_name).first()
    if existing:
        return existing
    identity = ENSIdentity(
        id=uuid.uuid4(),
        organization_id=org_id,
        asset_id=asset_id,
        edge_node_id=edge_node_id,
        ens_name=ens_name,
        label=label,
        parent_name=settings.ens_parent_name,
        identity_type=identity_type,
        issuance_mode=IssuanceMode.MOCK,
        status=IdentityStatus.RESERVED_NOT_ISSUED,
        public_metadata_json={},
    )
    db.add(identity)
    db.flush()
    return identity


def _ensure_demo_asset(db: Session, org: Organization, user: User) -> Asset:
    asset = (
        db.query(Asset)
        .filter(
            Asset.organization_id == org.id,
            Asset.public_asset_reference == "DOV-COMPUTE-000001",
        )
        .first()
    )
    if asset:
        return asset
    asset = Asset(
        id=uuid.uuid4(),
        organization_id=org.id,
        public_asset_reference="DOV-COMPUTE-000001",
        asset_class=AssetClass.COMPUTE_HARDWARE,
        category="GPU_ACCELERATOR",
        name="RTX PRO 6000 Blackwell Workstation GPU",
        description=(
            "Illustrative demo asset. NVIDIA RTX PRO 6000 Blackwell workstation "
            "GPU configuration · evidence intake stage."
        ),
        status=AssetStatus.EVIDENCE_INTAKE,
        client_internal_reference="DEMO-GPU-001",
        created_by=user.id,
    )
    db.add(asset)
    db.flush()
    db.add(
        ComputeAssetProfile(
            id=uuid.uuid4(),
            asset_id=asset.id,
            manufacturer="NVIDIA",
            model="RTX PRO 6000 Blackwell",
            gpu_count=1,
            vram_per_gpu_gb=96,
            cpu=None,
            ram_gb=None,
            operating_system="Ubuntu 24.04 LTS",
            condition_status=ConditionStatus.NEW,
            operational_status="OPERATIONAL",
            intended_use=IntendedUse.TRAINING,
        )
    )
    return asset


def _ensure_demo_proof_chain(db: Session, asset: Asset, user: User) -> DefendableDeed | None:
    """Build the full proof chain for the seeded asset · idempotent.

    Produces · in order ·
      1. an EvidenceItem with the canonical sample benchmark payload
      2. an EvidenceManifest (regenerated from current evidence set)
      3. an AIOVAnalysis · doctrine-correct draft narrative
      4. a ValidatorReview · runs the same 12 deterministic checks the
         live API does · should land PASSED_FOR_PACKAGING
      5. a DefendableDeed v1 · DRAFT_REVIEW_RECORD
      6. publish_public(deed) so /verify/{slug} resolves it

    If a publicly-published deed already exists for the asset, returns
    that deed without making any changes (so re-runs are no-ops).
    """
    existing = (
        db.query(DefendableDeed)
        .filter(DefendableDeed.asset_id == asset.id)
        .filter(DefendableDeed.is_public == True)  # noqa: E712
        .order_by(DefendableDeed.version.desc())
        .first()
    )
    if existing:
        return existing

    # ── 1. Evidence item ──────────────────────────────────────────────
    body = json.dumps(_SAMPLE_BENCHMARK, indent=2, sort_keys=True).encode("utf-8")
    digest = sha256_bytes(body)
    evidence = (
        db.query(EvidenceItem)
        .filter(EvidenceItem.asset_id == asset.id)
        .filter(EvidenceItem.sha256_hash == digest)
        .first()
    )
    if not evidence:
        evidence = EvidenceItem(
            id=uuid.uuid4(),
            organization_id=asset.organization_id,
            asset_id=asset.id,
            filename="sample_benchmark.json",
            storage_key=(
                f"organizations/{asset.organization_id}/assets/{asset.id}"
                f"/raw/seed_sample_benchmark.json"
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

    # ── 2. Evidence manifest ──────────────────────────────────────────
    # regenerate_manifest writes the row · we don't need to hold a ref.
    regenerate_manifest(db, asset)

    # ── 3. AIOV draft · doctrine-correct narrative ────────────────────
    narrative = (
        "AI-assisted AIOV draft for the seeded demo asset. Asset identity "
        "and configuration are supported by the supplied benchmark receipt. "
        "Public market comparable analysis has not been attached to this "
        "preview · the deed is generated for validator review only. "
        "AI-assisted draft only. Not a licensed appraisal. Not a warranty, "
        "certification, or authentication guarantee."
    )
    aiov_payload = {
        "analysis_type": "AI_ASSISTED_OPINION_OF_VALUE",
        "asset_reference": asset.public_asset_reference,
        "asset_class": asset.asset_class.value,
        "status": "GENERATED_FOR_VALIDATOR_REVIEW",
        "identity_summary": {
            "manufacturer": "NVIDIA",
            "model": "RTX PRO 6000 Blackwell",
            "configuration_confidence": "SUPPORTED_BY_SUBMITTED_EVIDENCE",
        },
        "evidence_basis": [
            {
                "source_id": str(evidence.id),
                "source_type": "PRIVATE_EVIDENCE",
                "evidence_type": "BENCHMARK_OUTPUT",
                "supports": "ASSET_CONTEXT",
                "sha256": digest,
            }
        ],
        "market_evidence": [],
        "value_opinion": {
            "display_status": "WITHHELD_PENDING_VALIDATOR_REVIEW",
            "currency": "USD",
            "range_low": None,
            "range_high": None,
            "notes": (
                "A public value range may be added only after evidence and "
                "comparable review."
            ),
        },
        "missing_evidence": ["PURCHASE_RECEIPT", "CONFIRMED_SALE_COMPARABLES"],
        "limitations": [
            "AI-assisted draft only",
            "Not a licensed appraisal",
            "Not a warranty, certification, or authentication guarantee",
        ],
    }
    aiov = AIOVAnalysis(
        id=uuid.uuid4(),
        asset_id=asset.id,
        version=1,
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

    # ── 4. Validator review · 12 deterministic checks ─────────────────
    results = run_deterministic_checks(db, asset, aiov)
    status_value = summarise(results)
    receipt = build_receipt(asset, aiov.version, results, status_value)
    review = ValidatorReview(
        id=uuid.uuid4(),
        asset_id=asset.id,
        aiov_analysis_id=aiov.id,
        version=1,
        status=ValidatorStatus(status_value),
        protocol="VALIDATE_THE_VALIDATOR",
        findings_json=receipt.get("blocking_findings", []),
        checks_json=receipt["checks"],
        receipt_sha256=receipt["receipt_sha256"],
        reviewed_by=user.id,
    )
    db.add(review)
    db.flush()

    if status_value != "PASSED_FOR_PACKAGING":
        # Seed shouldn't ship a non-passing validator review · log and skip
        # the deed creation. Local dev can still iterate manually.
        print(
            f"  [seed] validator returned {status_value} · skipping deed publication"
        )
        return None

    # ── 5. Defendable deed v1 + 6. publish_public ─────────────────────
    try:
        deed = create_deed(db, asset, issued_by_user_id=user.id)
    except Exception as exc:
        print(f"  [seed] create_deed failed: {exc}")
        return None
    publish_public(deed)
    db.flush()
    return deed


def _ensure_demo_edge_node(db: Session, org: Organization) -> EdgeNode:
    node = (
        db.query(EdgeNode)
        .filter(EdgeNode.organization_id == org.id, EdgeNode.node_slug == "box-01")
        .first()
    )
    if node:
        return node
    node = EdgeNode(
        id=uuid.uuid4(),
        organization_id=org.id,
        node_name="Defendable Box 01",
        node_slug="box-01",
        enrollment_status=EnrollmentStatus.ENROLLED_DEMO,
        software_version="0.1.0",
        hardware_summary_json={
            "platform": "Jetson Orin Nano Super 8GB",
            "os": "NVIDIA L4T Ubuntu",
            "purpose": "DEMO_REFERENCE_NODE",
        },
    )
    db.add(node)
    db.flush()
    return node


def seed() -> None:
    db = SessionLocal()
    try:
        user = _get_or_create_user(db)
        org = _get_or_create_org(db)
        _ensure_membership(db, org, user)

        _ensure_ens(
            db,
            org_id=org.id,
            ens_name=f"swarmbee.{settings.ens_parent_name}",
            label="swarmbee",
            identity_type=IdentityType.ORGANIZATION,
        )

        asset = _ensure_demo_asset(db, org, user)
        # Proposed asset-level ENS identity is reserved (not yet a deed).
        _ensure_ens(
            db,
            org_id=org.id,
            ens_name=f"asset-dov-compute-000001.swarmbee.{settings.ens_parent_name}",
            label="asset-dov-compute-000001",
            identity_type=IdentityType.ASSET,
            asset_id=asset.id,
        )

        edge_node = _ensure_demo_edge_node(db, org)
        _ensure_ens(
            db,
            org_id=org.id,
            ens_name=f"box-01.swarmbee.{settings.ens_parent_name}",
            label="box-01",
            identity_type=IdentityType.EDGE_NODE,
            edge_node_id=edge_node.id,
        )

        # ── full proof chain · evidence → manifest → AIOV → validator → deed
        deed = _ensure_demo_proof_chain(db, asset, user)

        db.commit()
        print("✓ Swarm & Bee Demo seed complete.")
        print(f"  user:   {user.email}  (password from DEMO_USER_PASSWORD)")
        print(f"  org:    {org.name}  ({org.ens_name})")
        print(f"  asset:  {asset.public_asset_reference}  ({asset.name})")
        print(f"  edge:   {edge_node.node_name}  (ENROLLED_DEMO)")
        if deed:
            print(
                f"  deed:   {deed.deed_reference}  ({deed.status.value}"
                f" · public_slug: {deed.public_slug})"
            )
            print(f"          record_hash:   {deed.record_hash}")
        else:
            print("  deed:   not seeded (validator did not pass)")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
