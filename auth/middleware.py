import jwt
from flask import request, jsonify, g
from .tokens import verify_access_token

def install_auth_middleware(app):
    @app.before_request
    def ban_tenant_id_in_api_payloads():
        if not request.path.startswith("/api/"):
            return
        if "tenant_id" in request.args:
            return jsonify({"error": "Do not send tenant_id; it is derived from auth."}), 400
        if request.is_json:
            data = request.get_json(silent=True) or {}
            if isinstance(data, dict) and "tenant_id" in data:
                return jsonify({"error": "Do not send tenant_id; it is derived from auth."}), 400

    @app.before_request
    def require_jwt_for_api():
        if request.method == "OPTIONS":
            return
        if not request.path.startswith("/api/"):
            return

        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return jsonify({"error": "missing Authorization: Bearer token"}), 401

        token = auth[len("Bearer "):].strip()
        try:
            claims = verify_access_token(token)
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "token expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "invalid token"}), 401

        g.user_id = int(claims["sub"])
        g.tenant_id = int(claims["tid"])