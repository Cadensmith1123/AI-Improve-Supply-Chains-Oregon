"""
Shared pytest fixtures for the entire test suite.

This conftest.py lives in `tests/` so its fixtures are available to every
sub-directory (unit/, integration/, auth/, business/, security/, smoke/).

Critical notes about the repo's import shape:
- `frontend_flask/app.py` does `sys.path.append('..')`, then imports modules
  with bare names (`import access_db`, `import logic`, `import auth.middleware`).
  Therefore the test fixtures must add BOTH the repo root and `frontend_flask/`
  to `sys.path` before `frontend_flask.app` is imported. Once that is done,
  `from frontend_flask.app import app` (or `import app` after a chdir) works.
- The middleware queries the auth_db on every request unless we sidestep
  `get_user_totp`. We do that by monkey-patching at module level for all
  integration tests that mint a JWT.
- The database access layer (`access_db` and `db.functions.*`) is the seam
  we mock at; we never reach MySQL from unit/integration/business/security
  tests in this suite.

Markers:
- `unit`: pure function, no Flask/DB/HTTP.
- `integration`: Flask test client with mocked DB.
- `auth`: auth flows (login/register/TOTP/anon/reset).
- `business`: trip-cost calculation/snapshot invariants.
- `security`: IDOR, XSS, JWT-expiry, CSRF.
- `requires_db`: hits a real MySQL — excluded from default run.
- `slow`: network/mapbox/smoke — excluded from default run.
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path
from types import ModuleType
from typing import Any, Dict, Iterator
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Path bootstrap: must run before any frontend_flask import is attempted.
#
# When this conftest is dropped into the repo at `tests/conftest.py`, the
# repo root is the parent of `tests/` and contains `frontend_flask/` and
# `db/`. That's the happy path.
#
# When this conftest is run from a sibling `tests-suite/` directory (e.g.
# for self-validation of this suite during development), the repo root may
# live elsewhere. We let the user override it via TEST_REPO_ROOT.
# ---------------------------------------------------------------------------
_CONFTEST_DIR = Path(__file__).resolve().parent
_OVERRIDE = os.environ.get("TEST_REPO_ROOT")

if _OVERRIDE:
    REPO_ROOT = Path(_OVERRIDE).resolve()
elif (_CONFTEST_DIR.parent / "frontend_flask").is_dir():
    # The expected drop-in case: tests/ sits inside the repo.
    REPO_ROOT = _CONFTEST_DIR.parent
else:
    # Fallback: walk upward looking for a frontend_flask sibling.
    REPO_ROOT = _CONFTEST_DIR.parent
    for candidate in (_CONFTEST_DIR.parent, *_CONFTEST_DIR.parents):
        if (candidate / "frontend_flask").is_dir():
            REPO_ROOT = candidate
            break

FRONTEND = REPO_ROOT / "frontend_flask"

for p in (str(REPO_ROOT), str(FRONTEND)):
    if p not in sys.path:
        sys.path.insert(0, p)

# Provide deterministic, test-only secrets BEFORE app import. The Flask app
# pulls these from env at module-import time.
os.environ.setdefault("JWT_SECRET", "test-jwt-secret-do-not-use-in-prod")
os.environ.setdefault("SECRET_KEY", "test-flask-secret-do-not-use-in-prod")
os.environ.setdefault("JWT_ISSUER", "local-food-app-test")
os.environ.setdefault("JWT_AUDIENCE", "local-food-api-test")
os.environ.setdefault("JWT_ACCESS_TTL_SECONDS", "3600")
os.environ.setdefault("ANON_RECOVERY_TTL_SECONDS", "604800")
os.environ.setdefault("MAPBOX_TOKEN", "test-mapbox-token-not-real")


# ---------------------------------------------------------------------------
# DB stub module
# ---------------------------------------------------------------------------
@pytest.fixture
def fake_db() -> MagicMock:
    """
    A MagicMock pre-shaped with sensible defaults for every access_db function
    used by the blueprints. Override per-test as needed.
    """
    db = MagicMock(name="access_db")

    # Reads — return empty/sane defaults so the dashboard renders.
    db.list_locations.return_value = []
    db.list_vehicles.return_value = []
    db.list_drivers.return_value = []
    db.list_products.return_value = []
    db.list_routes.return_value = []
    db.get_dashboard_data.return_value = {
        "routes": [],
        "vehicles": [],
        "drivers": [],
        "locations": [],
        "products": [],
    }
    db.get_all_routes_raw.return_value = []
    db.get_route.return_value = None
    db.get_route_raw.return_value = None
    db.get_vehicle.return_value = None
    db.get_driver.return_value = None
    db.get_product.return_value = None

    # Writes — success tuples by default.
    db.create_route.return_value = (True, None, 1)
    db.create_vehicle.return_value = (True, None, 1)
    db.create_driver.return_value = (True, None, 1)
    db.create_location.return_value = (True, None, 1)
    db.create_product.return_value = (True, None, "SKU-1")
    db.update_route.return_value = (True, None)
    db.update_vehicle.return_value = (True, None)
    db.update_driver.return_value = (True, None)
    db.update_location.return_value = (True, None)
    db.update_product.return_value = (True, None)
    db.delete_route.return_value = (True, None)
    db.delete_vehicle.return_value = (True, None)
    db.delete_driver.return_value = (True, None)
    db.delete_location.return_value = (True, None)
    db.delete_product.return_value = (True, None)
    db.assign_vehicle_to_route.return_value = (True, None)
    db.assign_driver_to_route.return_value = (True, None)
    db.add_product_to_route.return_value = (True, None)
    db.remove_product_from_route.return_value = (True, None)
    db.recalculate_route_costs.return_value = (True, None)
    db.export_routes_csv.return_value = None
    db.export_route_detailed_csv.return_value = None

    return db


# ---------------------------------------------------------------------------
# Flask app fixture
# ---------------------------------------------------------------------------
@pytest.fixture
def flask_app(fake_db: MagicMock, monkeypatch) -> Iterator[Any]:
    """
    Imports the Flask app with `access_db` and the auth helpers mocked.

    The app is reusable across requests in the same test, but we do NOT cache
    it across tests — the blueprints register module-level state that is
    awkward to undo (e.g., the in-memory rate-limit dict in auth_bp).
    """
    # Make sure the modules are freshly imported in this test so mocks take
    # effect. Wipe any cached app bits first, including the auth subpackage
    # so its `from .user_management import get_user_totp` re-binds to our
    # fresh stub.
    #
    # NOTE: We intentionally DO NOT wipe `logic` or `depreciation_insurance`.
    # They are pure modules with no state to reset. Wiping them creates two
    # divergent instances when test files have `import logic` at the top —
    # the cached top-of-file binding points at the pre-wipe instance, while
    # fixtures (e.g., mock_mapbox) patch the post-wipe instance.
    for modname in [
        "app", "access_db", "routes_bp", "products_bp", "assets_bp", "auth_bp",
        "map_route", "csv_template_bp", "location_import_bp",
        "products_import_bp", "drivers_import_bp", "vehicles_import_bp",
        "routes_import_bp",
        "auth", "auth.middleware", "auth.tokens", "auth.passwords",
        "auth.totp", "auth.user_management",
    ]:
        sys.modules.pop(modname, None)

    # Install access_db mock BEFORE app import so blueprints see it.
    sys.modules["access_db"] = fake_db

    # Stub the auth user_management functions so middleware does not touch
    # MySQL during tests. Tests that exercise these specifically will
    # re-patch with targeted return values.
    fake_user_mgmt = ModuleType("auth.user_management")
    fake_user_mgmt.get_user_by_username = MagicMock(return_value=None)
    fake_user_mgmt.create_user = MagicMock(return_value=1)
    fake_user_mgmt.set_totp_secret = MagicMock(return_value=None)
    fake_user_mgmt.get_user_totp_secret = MagicMock(return_value="JBSWY3DPEHPK3PXP")
    fake_user_mgmt.set_totp_confirmed = MagicMock(return_value=None)
    fake_user_mgmt.get_user_for_reset = MagicMock(return_value=None)
    fake_user_mgmt.update_user_password = MagicMock(return_value=None)
    fake_user_mgmt.create_anonymous_user = MagicMock(return_value=(99, 99))
    fake_user_mgmt.update_user_activity = MagicMock(return_value=None)
    fake_user_mgmt.upgrade_anonymous_user = MagicMock(return_value=None)
    # Default: middleware sees TOTP confirmed so it does not redirect.
    fake_user_mgmt.get_user_totp = MagicMock(
        return_value={"totp_secret": "JBSWY3DPEHPK3PXP", "totp_confirmed": True}
    )
    sys.modules["auth.user_management"] = fake_user_mgmt

    from app import app as flask_app_obj  # type: ignore[import-not-found]

    flask_app_obj.config.update(
        TESTING=True,
        JWT_SECRET=os.environ["JWT_SECRET"],
        SECRET_KEY=os.environ["SECRET_KEY"],
        JWT_ISSUER=os.environ["JWT_ISSUER"],
        JWT_AUDIENCE=os.environ["JWT_AUDIENCE"],
        JWT_ACCESS_TTL_SECONDS=int(os.environ["JWT_ACCESS_TTL_SECONDS"]),
        ANON_RECOVERY_TTL_SECONDS=int(os.environ["ANON_RECOVERY_TTL_SECONDS"]),
    )

    # Expose helpers so tests can find the stub easily.
    flask_app_obj._fake_user_mgmt = fake_user_mgmt
    flask_app_obj._fake_db = fake_db

    yield flask_app_obj


@pytest.fixture
def client(flask_app):
    """A bare Flask test client. No JWT cookie — requests will be redirected."""
    return flask_app.test_client()


# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------
def _mint_jwt(flask_app, *, user_id: int = 1, tenant_id: int = 1,
              username: str = "alice", is_anon: bool = False,
              expired: bool = False) -> str:
    """
    Mint a JWT bypassing the mint_access_token helper so we can fabricate
    expired tokens. Mirrors the structure the app expects.
    """
    import jwt as pyjwt

    now = int(time.time())
    payload = {
        "sub": str(user_id),
        "tid": str(tenant_id),
        "iat": now - (3600 if expired else 0),
        "exp": now - 10 if expired else now + 3600,
        "iss": flask_app.config["JWT_ISSUER"],
        "aud": flask_app.config["JWT_AUDIENCE"],
    }
    if username:
        payload["username"] = username
    if is_anon:
        payload["anon"] = True
    return pyjwt.encode(payload, flask_app.config["JWT_SECRET"], algorithm="HS256")


@pytest.fixture
def jwt_for():
    """A factory: jwt_for(app, user_id=1, tenant_id=1)."""
    return _mint_jwt


@pytest.fixture
def auth_client(flask_app, jwt_for):
    """A test client with a valid (logged-in, TOTP-confirmed) JWT cookie."""
    token = jwt_for(flask_app, user_id=1, tenant_id=1, username="alice")
    c = flask_app.test_client()
    c.set_cookie("token", token, domain="localhost")
    return c


@pytest.fixture
def anon_client(flask_app, jwt_for):
    """A test client with a valid anonymous JWT cookie."""
    token = jwt_for(flask_app, user_id=99, tenant_id=99,
                    username=None, is_anon=True)
    c = flask_app.test_client()
    c.set_cookie("token", token, domain="localhost")
    return c


@pytest.fixture
def expired_anon_client(flask_app, jwt_for):
    """An expired anonymous JWT (for recovery-cookie tests)."""
    token = jwt_for(flask_app, user_id=99, tenant_id=99,
                    username=None, is_anon=True, expired=True)
    c = flask_app.test_client()
    c.set_cookie("token", token, domain="localhost")
    return c


# ---------------------------------------------------------------------------
# Sample data factories
# ---------------------------------------------------------------------------
@pytest.fixture
def sample_route() -> Dict[str, Any]:
    """A canonical route dict as returned by db.get_route().

    Includes all the calculated fields the route_view.html template
    references so tests don't crash on undefined attributes.
    """
    return {
        "scenario_id": 42,
        "route_id": 7,
        "name": "Farm to Hub",
        "route_name": "Farm to Hub",
        "origin_location_id": 1,
        "dest_location_id": 2,
        "origin_address": "100 Farm Rd Salem OR",
        "dest_address": "200 Hub Way Portland OR",
        "origin_address_street": "100 Farm Rd",
        "origin_city": "Salem", "origin_state": "OR",
        "dest_address_street": "200 Hub Way",
        "dest_city": "Portland", "dest_state": "OR",
        "vehicle_id": 1, "driver_id": 1,
        "vehicle_name": "Truck 1", "driver_name": "Driver 1",
        "vehicle_mpg": 10.0, "gas_price": 4.0,
        "driver_drive_rate": 30.0, "driver_load_rate": 20.0,
        "daily_insurance": 5.0,
        "depreciation_per_mile": 0.2,
        "daily_maintenance_cost": 4.0,
        "plan_load_min": 30.0, "plan_unload_min": 30.0,
        "sales_amount": 1000.0,
        "base_sales_amount": 1000.0,
        "entered_revenue": 1000.0,
        "calculated_revenue": 1200.0,
        "calc_total_cost": 700.0,
        "manifest": [],
        # Calculated fields the route_view template references:
        "driver_drive_cost_est": 50.0,
        "driver_load_cost_est": 10.0,
        "driver_unload_cost_est": 10.0,
        "driver_cost_total_est": 70.0,
        "fuel_cost_est": 8.0,
        "depreciation_cost_est": 4.0,
        "total_cogs": 100.0,
        "total_weight_lbs": 200.0,
        "total_volume": 50.0,
        "total_distance_miles": 20.0,
        "drive_minutes_est": 60.0,
        "load_minutes_plan": 30.0,
        "unload_minutes_plan": 30.0,
        "driver_drive_rate_per_hr": 30.0,
        "driver_load_rate_per_hr": 20.0,
        "profit_est_entered": 300.0,
        "profit_est_calculated": 500.0,
        "margin_est_entered": 30.0,
        "margin_est_calculated": 41.67,
        "line_item_count": 0,
        "total_cost": 700.0,
        "run_date": "2026-01-01",
        "origin_name": "Farm", "dest_name": "Hub",
        "calc_driver_cost": 70.0, "calc_fuel_cost": 8.0,
        "calc_cogs": 100.0, "calc_vehicle_cost": 13.0,
        "driver_cost": 30.0, "load_cost": 20.0, "unload_cost": 20.0,
        "fuel_cost": 8.0, "depreciation_cost": 4.0, "insurance_cost": 5.0,
        "pricing": {
            "margin": [], "trip": {
                "net_trip_profit": 500.0, "total_margin": 600.0,
                "delivery_cost": 100.0, "needs_more_margin": 0.0,
                "delivery_pct_of_margin": 16.67,
            },
            "allocated_delivery": {"by_weight": [], "by_volume": []},
        },
    }


@pytest.fixture
def sample_manifest_item() -> Dict[str, Any]:
    """A canonical manifest item dict (as returned from the DB)."""
    return {
        "manifest_item_id": 1,
        "product_id": "SKU-1",
        "product_name": "Apples",
        "quantity_loaded": 10,
        "price_per_item": 2.0,
        "cost_per_item": 1.0,
        "items_per_unit": 1.0,
        "unit_weight_lbs": 5.0,
        "unit_volume": 1.0,
    }


@pytest.fixture
def mock_mapbox(monkeypatch):
    """Patch logic.fetch_mapbox_distance to return a deterministic (miles, min)."""
    def _set(miles=10.0, minutes=20.0):
        import logic
        monkeypatch.setattr(logic, "fetch_mapbox_distance",
                            lambda *a, **kw: (miles, minutes))
        return miles, minutes
    return _set


# ---------------------------------------------------------------------------
# Marker registration (mirrors pyproject.toml addition).
# ---------------------------------------------------------------------------
def pytest_configure(config):
    for marker in [
        "unit: pure-Python unit tests, no Flask/DB/HTTP",
        "integration: Flask test client with mocked DB",
        "auth: authentication and TOTP flows",
        "business: trip-cost and snapshot invariants",
        "security: IDOR, XSS, JWT-expiry, CSRF",
        "requires_db: hits a real MySQL — opt-in",
        "slow: network/mapbox/smoke — opt-in",
    ]:
        config.addinivalue_line("markers", marker)
