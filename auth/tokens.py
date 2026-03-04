import time
from typing import Any, Dict

import jwt
from flask import current_app

"""
Mints and validates JWT tokens for auth
"""

def mint_access_token(*, user_id: int, tenant_id: int) -> str:
    now = int(time.time())
    ttl = int(current_app.config["JWT_ACCESS_TTL_SECONDS"])

    # Standard JWT claims + custom tenant_id (tid)
    payload = {
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
    secret = current_app.config["JWT_SECRET"]

    claims = jwt.decode(
        token,
        secret,
        algorithms=["HS256"],
        issuer=current_app.config["JWT_ISSUER"],
        audience=current_app.config["JWT_AUDIENCE"],
        options={"require": ["exp", "iat", "sub"]},
    )

    if "tid" not in claims:
        raise jwt.InvalidTokenError("Missing tid claim")

    return claims
