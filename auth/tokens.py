# auth/tokens.py
from __future__ import annotations

import time
from typing import Any, Dict

import jwt
from flask import current_app


def mint_access_token(*, user_id: int, tenant_id: int) -> str:
    """
    Create a signed JWT access token.
    Claims:
      - sub: user_id
      - tid: tenant_id
      - iat/exp: issued/expiry timestamps
      - iss/aud: issuer/audience checks
    """
    now = int(time.time())
    ttl = int(current_app.config["JWT_ACCESS_TTL_SECONDS"])

    payload: Dict[str, Any] = {
        "sub": str(user_id),
        "tid": str(tenant_id),
        "iat": now,
        "exp": now + ttl,
        "iss": current_app.config["JWT_ISSUER"],
        "aud": current_app.config["JWT_AUDIENCE"],
    }

    secret = current_app.config["JWT_SECRET"]
    return jwt.encode(payload, secret, algorithm="HS256")


def verify_access_token(token: str) -> Dict[str, Any]:
    """
    Verify signature + standard claims (exp/iss/aud).
    Returns decoded claims dict on success.
    Raises jwt exceptions on failure.
    """
    secret = current_app.config["JWT_SECRET"]

    claims = jwt.decode(
        token,
        secret,
        algorithms=["HS256"],
        issuer=current_app.config["JWT_ISSUER"],
        audience=current_app.config["JWT_AUDIENCE"],
        options={"require": ["exp", "iat", "sub"]},
    )

    # Optional: enforce required tenant id claim
    if "tid" not in claims:
        raise jwt.InvalidTokenError("Missing tid claim")

    return claims
