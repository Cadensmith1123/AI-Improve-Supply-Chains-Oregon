"""
Authentication & Session Security:
  "anonymous recovery cookies must not allow privilege escalation."
"""

import time

import jwt as pyjwt
import pytest

from auth.tokens import sign_recovery_cookie


pytestmark = pytest.mark.auth


def _expired_token(flask_app, *, anon):
    now = int(time.time())
    payload = {
        "sub": "1", "tid": "1", "iat": now - 7200, "exp": now - 60,
        "iss": flask_app.config["JWT_ISSUER"],
        "aud": flask_app.config["JWT_AUDIENCE"],
    }
    if anon:
        payload["anon"] = True
    return pyjwt.encode(payload, flask_app.config["JWT_SECRET"], algorithm="HS256")


def test_real_user_expired_token_not_resurrected_by_recovery(flask_app):
    """A non-anon expired token must NOT be revived via an anon_recovery cookie."""
    with flask_app.app_context():
        rec = sign_recovery_cookie(1, 1)
    c = flask_app.test_client()
    c.set_cookie("token", _expired_token(flask_app, anon=False), domain="localhost")
    c.set_cookie("anon_recovery", rec, domain="localhost")
    resp = c.get("/routes", follow_redirects=False)
    assert resp.status_code in (302, 303)
    assert "logout" in resp.headers.get("Location", "")
