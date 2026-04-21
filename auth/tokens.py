import time
from typing import Any, Dict

import jwt
from flask import current_app
from itsdangerous import URLSafeTimedSerializer

"""
Mints and validates JWT tokens for auth
"""

def mint_access_token(*, user_id: int, tenant_id: int, username: str = None, is_anon: bool = False) -> str:
    now = int(time.time())
    ttl = int(current_app.config["JWT_ACCESS_TTL_SECONDS"])

    # Standard JWT claims + custom tenant_id (tid)
    payload = {
        "sub": str(user_id),
        "tid": str(tenant_id),
        "iat": now,
        "exp": now + ttl,
        "iss": current_app.config["JWT_ISSUER"],
        "aud": current_app.config["JWT_AUDIENCE"]
    }
    if username:
        payload["username"] = username
    if is_anon:
        payload["anon"] = True

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


def sign_reset_token(user_id):
    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return s.dumps({"uid": user_id, "purpose": "pw_reset"})


def verify_reset_token(token, max_age=600):  # 10 minutes
    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        data = s.loads(token, max_age=max_age)
        if data.get("purpose") != "pw_reset":
            return None
        return data["uid"]
    except Exception:
        return None