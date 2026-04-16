from flask import Blueprint, request, jsonify, current_app, render_template, redirect, url_for
from auth.tokens import mint_access_token, verify_access_token
from auth.passwords import verify_password, DUMMY_HASH
from auth.user_management import get_user_by_username, create_user, get_user_totp_secret, set_user_totp_secret, set_totp_confirmed
from auth.totp import generate_secret


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
    

@auth_bp.route("/totp/setup", methods=["GET"])
def totp_setup():
    secret = get_user_totp_secret(g.user_id)
    if not secret:
        secret = generate_secret()
        set_user_totp_secret(g.user_id, secret)
    return render_template("totp_setup.html", secret=secret)


@auth_bp.post("/totp/confirm")
def totp_confirm():
    code = request.form.get("code", "").strip()
    secret = get_user_totp_secret(g.user_id)
    if verify_code(secret, code):
        set_totp_confirmed(g.user_id, True)
        return redirect(url_for("routes.routes_list"))
    return render_template("totp_setup.html", secret=secret,
                           error="Invalid code. Make sure your authenticator shows a current code and try again.")