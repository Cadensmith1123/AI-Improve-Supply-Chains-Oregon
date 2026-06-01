"""
Security Testing / Black-Box:
  * /routes/<id>/view with another tenant's (or nonexistent) route_id -> 404.
  * Scoped writes never cross tenants: a mutation on a foreign route_id -> 404.
  * JWT with altered tenant_id -> no foreign data: tenant_id is taken ONLY from
    the verified JWT, never from a user-supplied query/form value.
"""

import pytest


pytestmark = pytest.mark.security


def test_foreign_or_missing_route_view_is_404(auth_client, fake_db):
    """Scoped read returns None (foreign or nonexistent) -> 404, never 200."""
    fake_db.get_route.return_value = None
    resp = auth_client.get("/routes/12345/view", follow_redirects=False)
    assert resp.status_code == 404


def test_query_param_tenant_id_is_ignored(auth_client, fake_db, sample_route):
    """A ?tenant_id= query param must not reach the data layer."""
    fake_db.get_route.return_value = sample_route
    auth_client.get("/routes/7/view?tenant_id=999")
    call = fake_db.get_route.call_args
    assert "tenant_id" not in call.kwargs
    assert 999 not in call.args and "999" not in call.args


def test_form_tenant_id_is_ignored(auth_client, fake_db):
    """A form 'tenant_id' field must not reach the data layer."""
    fake_db.create_route.return_value = (True, None, 1)
    auth_client.post("/routes/new", data={
        "origin_location_id": "1", "dest_location_id": "2",
        "sales_amount": "100", "tenant_id": "999",
    }, follow_redirects=False)
    call = fake_db.create_route.call_args
    assert "tenant_id" not in call.kwargs
    assert 999 not in call.args and "999" not in call.args


def test_mutation_on_foreign_route_is_404(auth_client, fake_db):
    """Scoped writes must not cross tenants: a mutation on a foreign/missing
    route_id is rejected as 404 before any change is attempted."""
    fake_db.get_route.return_value = None
    resp = auth_client.post("/routes/12345/assign-vehicle",
                            data={"vehicle_id": "5"}, follow_redirects=False)
    assert resp.status_code == 404
