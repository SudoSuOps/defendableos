from fastapi import APIRouter

from app.api.v1 import (
    admin_goods,
    admin_summary,
    auth,
    organizations,
    assets,
    evidence,
    research,
    aiov,
    validator,
    deeds,
    ens,
    edge,
    public,
    audit,
    claw_swarm,
    claw_bakery,
    marketplace_ebay_notifications,
    admin_ebay,
)

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth.router, tags=["auth"])
api_router.include_router(organizations.router, tags=["organizations"])
api_router.include_router(assets.router, tags=["assets"])
api_router.include_router(evidence.router, tags=["evidence"])
api_router.include_router(research.router, tags=["research"])
api_router.include_router(aiov.router, tags=["aiov"])
api_router.include_router(validator.router, tags=["validator"])
api_router.include_router(deeds.router, tags=["deeds"])
api_router.include_router(ens.router, tags=["ens"])
api_router.include_router(edge.router, tags=["edge"])
api_router.include_router(public.router, tags=["public"])
api_router.include_router(audit.router, tags=["audit"])
api_router.include_router(admin_goods.router, tags=["admin-goods"])
api_router.include_router(admin_summary.router, tags=["admin-summary"])
api_router.include_router(claw_swarm.router)
api_router.include_router(claw_bakery.router)
api_router.include_router(marketplace_ebay_notifications.router)
api_router.include_router(admin_ebay.router)
