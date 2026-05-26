"""Codex API/Fly exposure repair — verification tests.

These assert the repair at the logic/route-graph level (no in-process HTTP client, matching the
existing helper-test style). Authoritative live proof is the post-deploy public HTTP check.
"""
from __future__ import annotations

import os
import subprocess
import sys

import pytest
from fastapi import HTTPException

from app.api.v1 import admin_ebay, claw_bakery, claw_swarm, compute_claw
from app.core.deps import require_ebay_admin
from app.main import app, healthz

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

LEAK_KEYS = {
    "integrations", "model_provider", "brave_configured", "kimi_configured",
    "openai_configured", "swarmcurator_configured", "defendable_ledger_publisher_configured",
    "ebay_configured", "ens_mode", "kimi_model", "driver", "bakery_dirs",
}


def _route_dep_calls(route):
    """Names of every dependency callable wired into a route (decorator + params, recursive)."""
    names = set()
    dep = getattr(route, "dependant", None)
    stack = list(getattr(dep, "dependencies", [])) if dep else []
    while stack:
        d = stack.pop()
        if getattr(d, "call", None) is not None:
            names.add(getattr(d.call, "__name__", str(d.call)))
        stack.extend(getattr(d, "dependencies", []))
    return names


def _route(path_suffix, method="GET"):
    for r in app.routes:
        if getattr(r, "path", "").endswith(path_suffix) and method in getattr(r, "methods", set()):
            return r
    raise AssertionError(f"route not found: {method} ...{path_suffix}")


# 1. /healthz reveals no integration booleans
def test_healthz_no_integration_leakage():
    body = healthz()
    assert set(body) == {"status", "service", "version"}
    assert not (set(body) & LEAK_KEYS)


# 2/3. docs + openapi disabled under production-like config (fresh import in a subprocess)
def test_docs_and_openapi_disabled_in_production():
    code = (
        "import app.main as m;"
        "print(m.app.docs_url, m.app.redoc_url, m.app.openapi_url)"
    )
    out = subprocess.run([sys.executable, "-c", code], cwd=REPO,
                         env={**os.environ, "APP_ENV": "production"},
                         capture_output=True, text=True)
    assert out.returncode == 0, out.stderr
    assert out.stdout.strip() == "None None None", out.stdout


# 4/5 are covered live (auth requires a DB user); here we assert the gates exist on admin routers.
def test_admin_ebay_router_is_boundary_gated():
    dep_calls = {getattr(d.dependency, "__name__", "") for d in admin_ebay.router.dependencies}
    assert "require_ebay_admin" in dep_calls


# 6/7. admin-adjacent routes carry the gate (so unauth -> 401/503, not 422)
@pytest.mark.parametrize("suffix,method", [
    ("/admin/ebay/browse/search", "GET"),
    ("/compute-claw/admin/aiov-draft/compose", "POST"),
    ("/compute-claw/admin/readiness", "GET"),
    ("/admin/ebay/oauth/readiness", "GET"),
])
def test_admin_adjacent_routes_require_gate(suffix, method):
    assert "require_ebay_admin" in _route_dep_calls(_route(suffix, method))


# 8. approved public demo routes are NOT gated (intentionally public synthetic)
@pytest.mark.parametrize("suffix,method", [
    ("/compute-claw/intake", "POST"),
    ("/compute-claw/categories", "GET"),
    ("/agent-swarm/clawcheck/intake", "POST"),
    ("/claw-bakery/public-metrics", "GET"),
])
def test_public_demo_routes_not_gated(suffix, method):
    assert "require_ebay_admin" not in _route_dep_calls(_route(suffix, method))


# require_ebay_admin behavior: 503 when token unset (test env), and it reads the header
def test_require_ebay_admin_503_when_unset():
    with pytest.raises(HTTPException) as e:
        require_ebay_admin(x_ebay_admin_token=None)
    assert e.value.status_code in (401, 503)


def test_require_ebay_admin_401_on_bad_token(monkeypatch):
    import app.core.deps as deps
    monkeypatch.setattr(deps, "get_settings", lambda: type("S", (), {"ebay_admin_token": "secret"})())
    with pytest.raises(HTTPException) as e:
        deps.require_ebay_admin(x_ebay_admin_token="wrong")
    assert e.value.status_code == 401
    # correct token passes (returns None)
    assert deps.require_ebay_admin(x_ebay_admin_token="secret") is None


# 9/leakage. public healthchecks reveal no provider/driver leakage
def test_public_healthchecks_no_leakage():
    swarm = claw_swarm.healthcheck()
    assert not (set(swarm) & LEAK_KEYS), swarm
    bakery = claw_bakery.bakery_healthcheck()
    assert "driver" not in bakery and "bakery_dirs" not in bakery
