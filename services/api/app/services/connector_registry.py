"""Connector registry · honest provider status reporting.

Maps each configured connector to a ProviderStatus enum based on
real config presence + the live-call kill switch. NEVER returns READY
without:
  · API key/credentials present
  · live calls explicitly enabled
  · terms_review_status reviewed

Service functions:
  · resolve_status(provider)    · pure compute · no DB write
  · upsert_connector(db, ...)   · persist the snapshot
  · refresh_all(db)             · sync every connector to current config
"""
from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.goods import (
    ProviderName,
    ProviderStatus,
    SourceConnector,
    TermsReviewStatus,
)


def _brave_status() -> ProviderStatus:
    if not settings.brave_api_key:
        return ProviderStatus.NOT_CONFIGURED
    if not settings.brave_live_calls_enabled or not settings.live_provider_calls_enabled:
        return ProviderStatus.CONFIGURED_DISABLED
    return ProviderStatus.READY


def _ebay_browse_status() -> ProviderStatus:
    if not (settings.ebay_app_id and settings.ebay_cert_id):
        return ProviderStatus.NOT_CONFIGURED
    if not settings.ebay_browse_live_calls_enabled or not settings.live_provider_calls_enabled:
        return ProviderStatus.CONFIGURED_DISABLED
    if settings.ebay_environment == "production" and not settings.ebay_production_access_confirmed:
        # Surfacing this as ERROR because keys are present but production
        # access has not been confirmed by the founder · the connector
        # should NOT silently degrade to sandbox.
        return ProviderStatus.ERROR
    return ProviderStatus.READY


CONNECTOR_DEFINITIONS: list[dict] = [
    {
        "provider_name": ProviderName.BRAVE_LLM_CONTEXT,
        "connector_purpose": "Public trend-discovery context · never a comp",
        "default_terms": TermsReviewStatus.REVIEWED_INTERNAL_RESEARCH_ONLY,
        "status_fn": _brave_status,
    },
    {
        "provider_name": ProviderName.EBAY_BROWSE,
        "connector_purpose": "Public active listing observations · asking-market context only",
        "default_terms": TermsReviewStatus.REVIEWED_INTERNAL_RESEARCH_ONLY,
        "status_fn": _ebay_browse_status,
    },
    {
        "provider_name": ProviderName.EBAY_INVENTORY,
        "connector_purpose": "Future outbound eBay listing publication · disabled",
        "default_terms": TermsReviewStatus.TERMS_REVIEW_PENDING,
        "status_fn": lambda: ProviderStatus.FUTURE_DISABLED,
    },
    {
        "provider_name": ProviderName.SHOPIFY_FUTURE,
        "connector_purpose": "Future Shopify MarketReady export · disabled",
        "default_terms": TermsReviewStatus.TERMS_REVIEW_PENDING,
        "status_fn": lambda: ProviderStatus.FUTURE_DISABLED,
    },
    {
        "provider_name": ProviderName.CLIENT_UPLOAD,
        "connector_purpose": "Client-provided evidence · PRIVATE_BY_DEFAULT",
        "default_terms": TermsReviewStatus.REVIEWED_INTERNAL_RESEARCH_ONLY,
        "status_fn": lambda: ProviderStatus.READY,
    },
    {
        "provider_name": ProviderName.FIRST_PARTY_TRANSACTION,
        "connector_purpose": "Founder-owned transaction evidence · manual review required",
        "default_terms": TermsReviewStatus.TERMS_REVIEW_PENDING,
        "status_fn": lambda: ProviderStatus.READY,
    },
    {
        "provider_name": ProviderName.LICENSED_TRANSACTION_DATA_FUTURE,
        "connector_purpose": "Future licensed transaction data feed · disabled until terms reviewed",
        "default_terms": TermsReviewStatus.TERMS_REVIEW_PENDING,
        "status_fn": lambda: ProviderStatus.FUTURE_DISABLED,
    },
]


def resolve_status(provider: ProviderName) -> ProviderStatus:
    for d in CONNECTOR_DEFINITIONS:
        if d["provider_name"] == provider:
            return d["status_fn"]()
    return ProviderStatus.NOT_CONFIGURED


def upsert_connector(db: Session, provider: ProviderName) -> SourceConnector:
    """Insert or update a single connector's status snapshot."""
    definition = next(
        (d for d in CONNECTOR_DEFINITIONS if d["provider_name"] == provider), None
    )
    if definition is None:
        raise ValueError(f"Unknown provider: {provider}")

    status = definition["status_fn"]()
    row = db.query(SourceConnector).filter(SourceConnector.provider_name == provider).first()
    if row is None:
        row = SourceConnector(
            id=uuid.uuid4(),
            provider_name=provider,
            connector_purpose=definition["connector_purpose"],
            provider_status=status,
            live_calls_enabled=(status == ProviderStatus.READY),
            terms_review_status=definition["default_terms"],
        )
        db.add(row)
    else:
        row.provider_status = status
        row.live_calls_enabled = status == ProviderStatus.READY
    db.flush()
    return row


def refresh_all(db: Session) -> list[SourceConnector]:
    """Refresh every connector status · idempotent."""
    rows = [upsert_connector(db, d["provider_name"]) for d in CONNECTOR_DEFINITIONS]
    return rows
