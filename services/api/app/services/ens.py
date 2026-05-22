"""ENS identity service with pluggable adapters.

The mock adapter is fully functional for the MVP. CCIP-Read and onchain wrapped
adapters live behind admin-only flags and are intentionally minimal.
"""
from __future__ import annotations

import re
import uuid
from dataclasses import dataclass
from typing import Protocol

from slugify import slugify
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.ens import (
    ENSIdentity,
    IdentityStatus,
    IdentityType,
    IssuanceMode,
)


BLOCKED_LABELS = {
    "admin", "api", "app", "auth", "login", "support", "verify",
    "root", "registry", "resolver", "system", "www",
}


def normalise_label(raw: str) -> str:
    """Lowercase · ASCII · dashes only · no leading/trailing/double dashes."""
    slug = slugify(raw, lowercase=True, separator="-", regex_pattern=r"[^a-z0-9-]")
    slug = re.sub(r"-+", "-", slug).strip("-")
    if not slug:
        raise ValueError("label is empty after normalisation")
    if slug in BLOCKED_LABELS:
        raise ValueError(f"label '{slug}' is reserved")
    if not re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?", slug):
        raise ValueError(f"label '{slug}' is not a valid ENS label")
    return slug


@dataclass
class ReservationRequest:
    label: str
    parent: str
    identity_type: IdentityType
    organization_id: uuid.UUID
    asset_id: uuid.UUID | None = None
    deed_id: uuid.UUID | None = None
    edge_node_id: uuid.UUID | None = None
    public_metadata: dict | None = None


@dataclass
class ReservationResult:
    identity: ENSIdentity
    proposed_public_records: dict


class ENSAdapter(Protocol):
    mode: IssuanceMode

    def reserve(self, db: Session, req: ReservationRequest) -> ReservationResult: ...

    def issue(self, db: Session, identity: ENSIdentity) -> ENSIdentity: ...


class MockENSAdapter:
    """Reserves names in the DB. Never touches a chain or signer key."""

    mode = IssuanceMode.MOCK

    def reserve(self, db: Session, req: ReservationRequest) -> ReservationResult:
        label = normalise_label(req.label)
        full_name = f"{label}.{req.parent}"

        existing = db.query(ENSIdentity).filter(ENSIdentity.ens_name == full_name).first()
        if existing:
            raise ValueError(f"ENS name {full_name} is already reserved")

        identity = ENSIdentity(
            id=uuid.uuid4(),
            organization_id=req.organization_id,
            asset_id=req.asset_id,
            deed_id=req.deed_id,
            edge_node_id=req.edge_node_id,
            ens_name=full_name,
            label=label,
            parent_name=req.parent,
            identity_type=req.identity_type,
            issuance_mode=IssuanceMode.MOCK,
            status=IdentityStatus.RESERVED_NOT_ISSUED,
            public_metadata_json=req.public_metadata or {},
        )
        db.add(identity)
        db.flush()
        return ReservationResult(identity=identity, proposed_public_records={})

    def issue(self, db: Session, identity: ENSIdentity) -> ENSIdentity:
        raise RuntimeError(
            "MockENSAdapter does not issue live ENS records. Enable an onchain or "
            "offchain adapter, set ENS_LIVE_WRITES_ENABLED=true, and re-run from "
            "the admin console."
        )


class OffchainCCIPAdapter:
    """Future · resolves wildcards via CCIP-Read gateway. Not implemented for MVP."""

    mode = IssuanceMode.OFFCHAIN_CCIP

    def reserve(self, db: Session, req: ReservationRequest) -> ReservationResult:
        # Identical reservation semantics to mock · issuance is the divergence point.
        return MockENSAdapter().reserve(db, req)

    def issue(self, db: Session, identity: ENSIdentity) -> ENSIdentity:
        raise NotImplementedError("OffchainCCIPAdapter.issue · not implemented yet.")


class OnchainWrappedSubnameAdapter:
    """Future · ENS NameWrapper subname mint. Admin-only, double-gated."""

    mode = IssuanceMode.ONCHAIN_WRAPPED

    def reserve(self, db: Session, req: ReservationRequest) -> ReservationResult:
        return MockENSAdapter().reserve(db, req)

    def issue(self, db: Session, identity: ENSIdentity) -> ENSIdentity:
        if not settings.ens_live_writes_enabled:
            raise RuntimeError(
                "ENS_LIVE_WRITES_ENABLED is false. Live issuance requires admin opt-in."
            )
        if not settings.ens_signer_private_key:
            raise RuntimeError("ENS_SIGNER_PRIVATE_KEY is not configured.")
        raise NotImplementedError(
            "OnchainWrappedSubnameAdapter.issue · transaction signing not implemented."
        )


def get_adapter() -> ENSAdapter:
    mode = (settings.ens_mode or "mock").lower()
    if mode == "mock":
        return MockENSAdapter()
    if mode == "offchain_ccip":
        return OffchainCCIPAdapter()
    if mode == "onchain_wrapped":
        return OnchainWrappedSubnameAdapter()
    return MockENSAdapter()


def build_public_metadata_for_deed(
    record_hash: str, manifest_hash: str, validator_receipt_hash: str, verify_url: str
) -> dict:
    return {
        "com.defendable.type": "DEFENDABLE_DEED",
        "com.defendable.version": "0.1",
        "com.defendable.status": "PUBLIC_VERIFICATION_AVAILABLE",
        "com.defendable.verify_url": verify_url,
        "com.defendable.record_hash": record_hash,
        "com.defendable.manifest_hash": manifest_hash,
        "com.defendable.validator_receipt_hash": validator_receipt_hash,
    }
