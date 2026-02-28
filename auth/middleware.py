import jwt
from flask import request, jsonify, g
from .tokens import verify_access_token

def install_auth_middleware(app):
    @app.before_request
    def ban_tenant_id_in_api_payloads():
        """Security: Prevent clients from injecting tenant_id."""
        if not request.path.startswith("/api/"):
            return
            
        has_arg = "tenant_id" in request.args
        has_json = request.is_json and isinstance(request.get_json(silent=True), dict) and "tenant_id" in request.get_json(silent=True)
        
        if has_arg or has_json:
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
            g.user_id = int(claims["sub"])
            g.tenant_id = int(claims["tid"])
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
            return jsonify({"error": "Invalid or expired token"}), 401