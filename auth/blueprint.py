from flask import Blueprint, request, jsonify
from .tokens import mint_access_token
from .passwords import verify_password, DUMMY_HASH
from .user_management import get_user_by_username

auth_bp = Blueprint("auth", __name__)

@auth_bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "username and password required"}), 400

    user = get_user_by_username(username)
    
    # Mitigate timing attacks: Always verify a hash, even if user is not found.
    target_hash = user["password_hash"] if user else DUMMY_HASH
    
    if not verify_password(target_hash, password) or not user:
        return jsonify({"error": "invalid credentials"}), 401

    token = mint_access_token(user_id=user["user_id"], tenant_id=user["tenant_id"])
    return jsonify({"token": token})