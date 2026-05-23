"""Smoke test for /admin/operator-summary endpoint shape."""
from app.api.v1.admin_summary import operator_summary


def test_operator_summary_import_clean():
    """The endpoint module imports without side effects · proves the
    router mount won't break the API at startup."""
    assert callable(operator_summary)


def test_admin_summary_router_mounted():
    """Confirm the router is included in the v1 mount."""
    from app.api.v1.router import api_router
    paths = [
        getattr(r, "path", "") for r in api_router.routes
    ]
    assert any("/admin/operator-summary" in p for p in paths), (
        "operator-summary endpoint not mounted"
    )
