"""DefendableOS API entrypoint."""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings

# Codex exposure repair: public OpenAPI/docs are disabled in production-like deployments so the
# full operational API (78 paths) is not anonymously browsable. Docs remain on in dev/test.
_docs_enabled = settings.app_env != "production"

app = FastAPI(
    title="DefendableOS API",
    description=(
        "Proof of Value · Validate the Validator. "
        "Evidence-backed asset records with AIOV analysis, validator receipts, "
        "Defendable Deeds, ENS reservation, and Defendable Box edge enrollment."
    ),
    version="0.1.0",
    docs_url="/docs" if _docs_enabled else None,
    redoc_url="/redoc" if _docs_enabled else None,
    openapi_url="/openapi.json" if _docs_enabled else None,
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
    # Codex exposure repair: liveness only. No integration booleans, provider names, storage
    # driver, eBay environment, or ENS mode are exposed to anonymous callers. Detailed readiness
    # lives behind the admin gate.
    return {
        "status": "ok",
        "service": "defendableos-api",
        "version": "0.1.0",
    }


app.include_router(api_router)
