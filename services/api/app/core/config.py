"""Centralised configuration · all secrets server-side · no surprises."""
from __future__ import annotations

from functools import lru_cache
from typing import Literal

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

    # Database
    database_url: str = (
        "postgresql+psycopg://defendable:defendable@localhost:5432/defendableos"
    )

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Object storage (S3-compatible · MinIO local)
    s3_endpoint_url: str = "http://localhost:9000"
    s3_access_key_id: str = "minioadmin"
    s3_secret_access_key: str = "minioadmin"
    s3_private_bucket: str = "defendable-private"
    s3_public_bucket: str = "defendable-public"
    s3_region: str = "us-east-1"

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
