"""
Security Testing:
  * totp_confirmed = False -> redirect to TOTP setup.
"""

import pytest


pytestmark = pytest.mark.auth


def _client(flask_app, jwt_for, **claims):
    c = flask_app.test_client()
    c.set_cookie("token", jwt_for(flask_app, **claims), domain="localhost")
    return c


def test_unconfirmed_totp_redirects_to_setup(flask_app, jwt_for):
    flask_app._fake_user_mgmt.get_user_totp.return_value = {
        "totp_secret": "SECRET", "totp_confirmed": False}
    resp = _client(flask_app, jwt_for, user_id=1, tenant_id=1,
                   username="alice").get("/routes", follow_redirects=False)
    assert resp.status_code in (302, 303)
    assert "totp" in resp.headers.get("Location", "")


def test_confirmed_totp_allows_request(flask_app, jwt_for):
    flask_app._fake_user_mgmt.get_user_totp.return_value = {
        "totp_secret": "SECRET", "totp_confirmed": True}
    resp = _client(flask_app, jwt_for, user_id=1, tenant_id=1,
                   username="alice").get("/routes")
    assert resp.status_code == 200
