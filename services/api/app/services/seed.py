"""Seed Swarm & Bee Demo · the founder-demo organization.

Idempotent. Safe to run multiple times. Creates:
  - demo user + ORG_ADMIN membership
  - Swarm & Bee Demo organization
  - swarmbee.defendable.eth reservation (mock, RESERVED_NOT_ISSUED)
  - RTX PRO 6000 Blackwell asset · DOV-COMPUTE-000001 · EVIDENCE_INTAKE
  - Defendable Box 01 edge node + box-01.swarmbee.defendable.eth reservation
"""
from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.asset import (
    Asset,
    AssetClass,
    AssetStatus,
    ComputeAssetProfile,
    ConditionStatus,
    IntendedUse,
)
from app.models.edge import EdgeNode, EnrollmentStatus
from app.models.ens import (
    ENSIdentity,
    IdentityStatus,
    IdentityType,
    IssuanceMode,
)
from app.models.organization import (
    ENSStatus,
    Organization,
    OrganizationMembership,
    OrgRole,
)
from app.models.user import User


DEMO_ORG_SLUG = "swarmbee"
DEMO_ORG_NAME = "Swarm & Bee Demo"


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

        db.commit()
        print("✓ Swarm & Bee Demo seed complete.")
        print(f"  user:   {user.email}  (password from DEMO_USER_PASSWORD)")
        print(f"  org:    {org.name}  ({org.ens_name})")
        print(f"  asset:  {asset.public_asset_reference}  ({asset.name})")
        print(f"  edge:   {edge_node.node_name}  (ENROLLED_DEMO)")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
