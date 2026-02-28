from flask import Blueprint, request, jsonify
from .tokens import mint_access_token
from .passwords import verify_password, DUMMY_HASH
from .user_management import get_user_by_username, create_user

auth_bp = Blueprint("auth", __name__)

@auth_bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "Username and password required"}), 400

    user = get_user_by_username(username)
    
    # Timing attack mitigation: Always verify a hash
    target_hash = user["password_hash"] if user else DUMMY_HASH
    if not user or not verify_password(target_hash, password):
        return jsonify({"error": "Invalid credentials"}), 401

    token = mint_access_token(user_id=user["user_id"], tenant_id=user["tenant_id"])
    return jsonify({"token": token})

@auth_bp.post("/register")
def register():
    data = request.get_json(silent=True) or {}
    username = data.get("username")
    password = data.get("password")
    email = data.get("email")

    if not username or not password or not email:
        return jsonify({"error": "Username, email, and password are required."}), 400

    try:
        user_id = create_user(username=username, password=password, email=email)
        
        if not user_id:
            return jsonify({"error": "Failed to create user."}), 500
            
        return jsonify({"message": "User created successfully."}), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        print(f"Registration Error: {e}")
        return jsonify({"error": "An unexpected error occurred."}), 500