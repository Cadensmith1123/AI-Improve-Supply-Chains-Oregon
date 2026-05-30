"""
Black-Box / Boundary:
  "All protected endpoints without a valid JWT — assert redirect to /auth/login."

(The middleware redirects unauthenticated requests to /logout, which clears
state and then redirects to /auth/login.)
"""

import pytest


pytestmark = pytest.mark.security


PROTECTED_GET_ENDPOINTS = [
    "/routes",
    "/routes/1/view",
    "/routes/1/edit",
    "/products",
    "/products/new",
]


@pytest.mark.parametrize("path", PROTECTED_GET_ENDPOINTS)
def test_protected_endpoint_without_jwt_redirects_to_auth(client, path):
    """No token cookie -> redirect into the auth flow, never served."""
    resp = client.get(path, follow_redirects=False)
    assert resp.status_code in (302, 303), f"{path} did not redirect"
    location = resp.headers.get("Location", "")
    assert "logout" in location or "login" in location
