"""Centralised configuration · all secrets server-side · no surprises."""
from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../../.env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # App
    app_env: Literal["development", "production", "test"] = "development"
    app_name: str = "DefendableOS"
    api_base_url: str = "http://localhost:8000"
    web_base_url: str = "http://localhost:3000"

    # Database · normalised to SQLAlchemy 2.0 + psycopg3 dialect form regardless
    # of what the host sets (Fly Managed Postgres hands out `postgresql://...`,
    # Heroku-style providers use `postgres://...`, our local docker-compose
    # specifies the dialect explicitly).
    database_url: str = (
        "postgresql+psycopg://defendable:defendable@localhost:5432/defendableos"
    )

    @field_validator("database_url")
    @classmethod
    def _normalize_db_url(cls, v: str) -> str:
        """Coerce postgres:// or postgresql:// into postgresql+psycopg:// so
        SQLAlchemy 2.0 can pick the psycopg3 driver. Idempotent · skips when
        an explicit `+driver` scheme is already specified."""
        if not v:
            return v
        scheme, _, rest = v.partition("://")
        if not rest:
            return v
        # Already specifies a driver · trust the operator.
        if "+" in scheme:
            return v
        if scheme == "postgres":
            return f"postgresql+psycopg://{rest}"
        if scheme == "postgresql":
            return f"postgresql+psycopg://{rest}"
        return v

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Object storage (S3-compatible · MinIO local · Tigris production)
    # OBJECT_STORAGE_PROVIDER toggles the adapter only · the wire protocol is
    # identical (S3 v4 sigv4) so the same boto3 client speaks to both. The
    # bucket names are split into 4 disclosure-boundary buckets per
    # GOODS_INTELLIGENCE_ARCHITECTURE.md.
    object_storage_provider: Literal["minio", "tigris", "s3"] = "minio"
    object_storage_live_enabled: bool = False
    s3_endpoint_url: str = "http://localhost:9000"
    s3_access_key_id: str = "minioadmin"
    s3_secret_access_key: str = "minioadmin"
    s3_region: str = "us-east-1"
    s3_presigned_url_ttl_seconds: int = 900
    # Legacy 2-bucket pair (kept for existing deed/evidence code paths)
    s3_private_bucket: str = "defendable-private"
    s3_public_bucket: str = "defendable-public"
    # New 4-bucket goods intelligence layout
    s3_private_evidence_bucket: str = "defendable-private-evidence-prod"
    s3_market_observations_bucket: str = "defendable-market-observations-prod"
    s3_derived_datasets_bucket: str = "defendable-derived-datasets-prod"
    s3_public_assets_bucket: str = "defendable-public-assets-prod"

    # Auth
    jwt_secret: str = "CHANGE_ME_IN_PRODUCTION"
    session_secret: str = "CHANGE_ME_IN_PRODUCTION"
    jwt_algorithm: str = "HS256"
    jwt_expires_minutes: int = 720

    # Brave LLM Context API
    brave_api_key: str = ""
    brave_llm_context_url: str = "https://api.search.brave.com/res/v1/llm/context"

    # eBay · Browse API for active listings · Marketplace Insights for sold comps.
    # Swarm & Bee business account · OAuth2 client_credentials flow (no user consent).
    ebay_app_id: str = ""          # aka Client ID
    ebay_cert_id: str = ""         # aka Client Secret
    ebay_dev_id: str = ""          # Dev account ID
    ebay_environment: str = "production"  # 'production' or 'sandbox'
    ebay_marketplace_id: str = "EBAY_US"  # EBAY_US · EBAY_GB · EBAY_DE · etc.

    # eBay · Marketplace Account Deletion notification endpoint · regulatory.
    # See app/api/v1/marketplace_ebay_notifications.py +
    #     app/services/compliance/ebay_account_deletion.py
    # NEVER commit a real token to source · token is read from env / Fly secret.
    ebay_account_deletion_endpoint: str = (
        "https://api.defendableos.com/api/v1/marketplace/ebay/notifications/account-deletion"
    )
    ebay_account_deletion_verification_token: str = ""
    ebay_account_deletion_notifications_enabled: bool = False

    # Model gateway · provider-agnostic. Switch with MODEL_PROVIDER=kimi|openai.
    model_provider: str = "kimi"

    # ── Kimi K2.6 (Moonshot · OpenAI-compatible) ──
    moonshot_api_key: str = ""
    moonshot_base_url: str = "https://api.moonshot.ai/v1"
    moonshot_model: str = "kimi-k2.6"
    kimi_thinking_default: Literal["enabled", "disabled"] = "disabled"

    # ── OpenAI ──
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o"
    openai_organization: str = ""

    # ENS · defendable.eth
    ens_parent_name: str = "defendable.eth"
    ens_mode: Literal["mock", "offchain_ccip", "onchain_wrapped"] = "mock"
    ens_live_writes_enabled: bool = False
    ens_rpc_url: str = ""
    ens_chain_id: int | None = None
    ens_resolver_address: str = ""
    ens_signer_private_key: str = ""  # MUST never leave the server

    # Edge appliance
    edge_enrollment_secret: str = "CHANGE_ME_IN_PRODUCTION"
    edge_token_ttl_minutes: int = 30

    # Public verification
    public_verification_enabled: bool = True

    # Goods Intelligence · live ingestion kill switches.
    # ALL default OFF · no third-party API gets called without the founder
    # explicitly setting the env var locally AND the connector being in
    # READY state.
    live_ingestion_enabled: bool = False
    live_provider_calls_enabled: bool = False
    public_marketing_exports_enabled: bool = False
    ens_publishing_enabled: bool = False
    brave_live_calls_enabled: bool = False
    brave_discovery_enabled: bool = False
    brave_max_calls_per_run: int = 1
    brave_max_context_tokens: int = 6000
    brave_context_threshold_mode: str = "strict"
    ebay_browse_live_calls_enabled: bool = False
    ebay_max_calls_per_run: int = 1
    ebay_production_access_confirmed: bool = False
    ebay_outbound_listing_enabled: bool = False
    pgvector_enabled: bool = False
    postgis_enabled: bool = False

    # Semrush · ProductRadar competitive-intelligence rail (added 2026-05-22).
    # All endpoints default OFF · founder verifies plan tier before flipping.
    semrush_api_key: str = ""
    semrush_live_calls_enabled: bool = False
    semrush_max_calls_per_run: int = 1
    semrush_seo_api_enabled: bool = False
    semrush_trends_api_enabled: bool = False
    semrush_ecommerce_keyword_analytics_enabled: bool = False
    semrush_rights_status: str = "TERMS_REVIEW_PENDING"
    semrush_data_use: str = "INTERNAL_RESEARCH_ONLY"
    semrush_model_training_export_enabled: bool = False

    # Demo affordances
    seed_demo_data: bool = True
    demo_user_email: str = "demo@swarmandbee.ai"
    demo_user_password: str = "defendable-demo"

    # ── Convenience flags for the UI ──
    @property
    def brave_configured(self) -> bool:
        return bool(self.brave_api_key)

    @property
    def kimi_configured(self) -> bool:
        return bool(self.moonshot_api_key)

    @property
    def openai_configured(self) -> bool:
        return bool(self.openai_api_key)

    @property
    def ebay_configured(self) -> bool:
        return bool(self.ebay_app_id and self.ebay_cert_id)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
