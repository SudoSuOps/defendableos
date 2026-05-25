"""DefendableOS API entrypoint."""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings

app = FastAPI(
    title="DefendableOS API",
    description=(
        "Proof of Value · Validate the Validator. "
        "Evidence-backed asset records with AIOV analysis, validator receipts, "
        "Defendable Deeds, ENS reservation, and Defendable Box edge enrollment."
    ),
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        # local dev
        settings.web_base_url,
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:4173",
        # production landing + subdomains (where ledger UI calls /public/lookup from)
        "https://defendableos.com",
        "https://www.defendableos.com",
        "https://ledger.defendableos.com",
        "https://verify.defendableos.com",
        "https://app.defendableos.com",
        "https://box.defendableos.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/healthz")
def healthz() -> dict:
    return {
        "status": "ok",
        "service": "defendableos-api",
        "version": "0.1.0",
        "integrations": {
            "model_provider": settings.model_provider,
            "brave_configured": settings.brave_configured,
            "kimi_configured": settings.kimi_configured,
            "openai_configured": settings.openai_configured,
            "swarmcurator_configured": settings.swarmcurator_configured,
            "ebay_configured": settings.ebay_configured,
            "ens_mode": settings.ens_mode,
            "ens_live_writes_enabled": settings.ens_live_writes_enabled,
        },
    }


app.include_router(api_router)
