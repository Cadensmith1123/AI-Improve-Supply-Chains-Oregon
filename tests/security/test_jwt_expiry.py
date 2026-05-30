"""
Security Testing:
  * Tampered JWT (wrong secret) -> logout redirect.
  * Expired access token -> logout redirect.
  * Malformed token / missing tid claim -> logout redirect.
"""

import time

import jwt as pyjwt
import pytest


pytestmark = pytest.mark.security


def _token(flask_app, *, exp_offset, secret=None):
    now = int(time.time())
    payload = {
        "sub": "1", "tid": "1", "iat": now, "exp": now + exp_offset,
        "iss": flask_app.config["JWT_ISSUER"],
        "aud": flask_app.config["JWT_AUDIENCE"],
    }
    return pyjwt.encode(payload, secret or flask_app.config["JWT_SECRET"],
                        algorithm="HS256")


def _get_routes(flask_app, token):
    c = flask_app.test_client()
    c.set_cookie("token", token, domain="localhost")
    return c.get("/routes", follow_redirects=False)


def test_expired_token_redirects_to_logout(flask_app):
    resp = _get_routes(flask_app, _token(flask_app, exp_offset=-3600))
    assert resp.status_code in (302, 303)
    assert "logout" in resp.headers.get("Location", "")


def test_wrong_secret_token_redirects_to_logout(flask_app):
    resp = _get_routes(flask_app, _token(flask_app, exp_offset=3600,
                                         secret="WRONG-SECRET"))
    assert resp.status_code in (302, 303)
    assert "logout" in resp.headers.get("Location", "")


def test_missing_tid_claim_redirects_to_logout(flask_app):
    """A validly-signed token with no tid claim is rejected (tenant required)."""
    now = int(time.time())
    no_tid = pyjwt.encode(
        {"sub": "1", "iat": now, "exp": now + 3600,
         "iss": flask_app.config["JWT_ISSUER"],
         "aud": flask_app.config["JWT_AUDIENCE"]},
        flask_app.config["JWT_SECRET"], algorithm="HS256",
    )
    resp = _get_routes(flask_app, no_tid)
    assert resp.status_code in (302, 303)
    assert "logout" in resp.headers.get("Location", "")


def test_garbage_token_redirects_to_logout(flask_app):
    """A non-JWT cookie value is rejected cleanly, not 500'd."""
    resp = _get_routes(flask_app, "not.a.real.jwt")
    assert resp.status_code in (302, 303)
    assert "logout" in resp.headers.get("Location", "")
