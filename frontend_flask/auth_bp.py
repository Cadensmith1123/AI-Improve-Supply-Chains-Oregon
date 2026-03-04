from flask import Blueprint, request, jsonify, current_app, render_template, redirect, url_for
from .tokens import mint_access_token, verify_access_token
from .passwords import verify_password, DUMMY_HASH
from .user_management import get_user_by_username, create_user

"""
Handles the API endpoints for Authentication (Login/Register).
"""

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        if request.cookies.get('token'):
            try:
                verify_access_token(request.cookies.get('token'))
                return redirect(url_for('home'))
            except:
                pass
        return render_template('login.html')

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

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        if request.cookies.get('token'):
            return redirect(url_for('home'))
        return render_template('register.html')

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
        current_app.logger.error(f"Registration Error: {e}")
        return jsonify({"error": "An unexpected error occurred."}), 500