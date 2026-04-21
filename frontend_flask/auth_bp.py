from flask import Blueprint, request, jsonify, current_app, render_template, redirect, url_for, g, make_response
from auth.passwords import verify_password, DUMMY_HASH, hash_password
from auth.user_management import get_user_by_username, create_user, set_totp_secret, get_user_totp_secret
from auth.user_management import set_totp_confirmed, get_user_for_reset, update_user_password
from auth.totp import generate_secret, verify_code, get_totp_uri, generate_qr_base64
from auth.tokens import mint_access_token, verify_access_token, sign_reset_token, verify_reset_token
from collections import defaultdict
from time import time

#Rate limiting arguments for password reset auth
_reset_rate = defaultdict(list)
RESET_LIMIT = 5
RESET_WINDOW = 3600


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

    token = mint_access_token(user_id=user["user_id"], tenant_id=user["tenant_id"], username=username)
    return jsonify({"token": token})

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        if request.cookies.get('token'):
            return redirect(url_for('home'))
        return render_template('register.html')

    # POST — traditional form submission
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "").strip()
    email = request.form.get("email", "").strip()

    if not username or not password or not email:
        return render_template('register.html',
                               error="Username, email, and password are required.",
                               form_data={"username": username, "email": email})

    try:
        user_id = create_user(username=username, password=password, email=email)
        if not user_id:
            return render_template('register.html',
                                   error="Failed to create user.",
                                   form_data={"username": username, "email": email})

        # Look up the new user to get tenant_id
        user = get_user_by_username(username)

        # Generate TOTP secret for password recovery
        secret = generate_secret()
        set_totp_secret(user_id, secret)

        # Mint JWT with username claim (needed for TOTP QR code generation)
        token = mint_access_token(user_id=user["user_id"], tenant_id=user["tenant_id"], username=username)
        resp = make_response(redirect(url_for("auth.totp_setup")))
        resp.set_cookie("token", token, httponly=True, samesite="Lax", max_age=3600)
        return resp

    except ValueError as e:
        return render_template('register.html',
                               error=str(e),
                               form_data={"username": username, "email": email})
    except Exception as e:
        current_app.logger.error(f"Registration Error: {e}")
        return render_template('register.html',
                               error="An unexpected error occurred.",
                               form_data={"username": username, "email": email})
    

@auth_bp.route("/totp/setup", methods=["GET"])
def totp_setup():
    secret = get_user_totp_secret(g.user_id)
    if not secret:
        secret = generate_secret()
        set_totp_secret(g.user_id, secret)

    # Generate QR code — username comes from g.username (set by middleware from JWT claim)
    uri = get_totp_uri(secret, g.username)
    qr_base64 = generate_qr_base64(uri)

    return render_template("totp_setup.html", secret=secret, qr_base64=qr_base64)


@auth_bp.post("/totp/confirm")
def totp_confirm():
    code = request.form.get("code", "").strip()
    secret = get_user_totp_secret(g.user_id)
    if verify_code(secret, code):
        set_totp_confirmed(g.user_id, True)
        return redirect(url_for("routes.routes_list"))

    # Re-generate QR for re-render on error
    uri = get_totp_uri(secret, g.username)
    qr_base64 = generate_qr_base64(uri)

    return render_template("totp_setup.html", secret=secret, qr_base64=qr_base64,
                           error="Invalid code. Make sure your authenticator shows a current code and try again.")


@auth_bp.route("/reset", methods=["GET"])
def reset_password_form():
    return render_template("reset_password.html")


@auth_bp.post("/reset/verify")
def reset_password_verify():
    username = request.form.get("username", "").strip()
    code = request.form.get("code", "").strip()

    if not check_reset_rate(username):
        return render_template("reset_password.html",
                               error="Too many attempts. Try again later.")

    user = get_user_for_reset(username)
    if not user or not user["totp_confirmed"]:
        return render_template("reset_password.html",
                               error="Invalid username or code.")

    if not verify_code(user["totp_secret"], code):
        return render_template("reset_password.html",
                               error="Invalid username or code.")

    reset_token = sign_reset_token(user["user_id"])
    return render_template("reset_new_password.html", reset_token=reset_token)


@auth_bp.post("/reset/complete")
def reset_password_complete():
    token = request.form.get("reset_token")
    new_password = request.form.get("new_password", "").strip()
    confirm_password = request.form.get("confirm_password", "").strip()

    if new_password != confirm_password:
        return render_template("reset_new_password.html",
                               reset_token=token, error="Passwords do not match.")

    user_id = verify_reset_token(token)
    if not user_id:
        return render_template("reset_password.html",
                               error="Reset session expired. Start over.")

    try:
        hashed = hash_password(new_password)
    except ValueError as e:
        return render_template("reset_new_password.html",
                               reset_token=token, error=str(e))

    update_user_password(user_id, hashed)
    return redirect(url_for("auth.login"))



def check_reset_rate(username):
    now = time()
    _reset_rate[username] = [t for t in _reset_rate[username] if now - t < RESET_WINDOW]
    if len(_reset_rate[username]) >= RESET_LIMIT:
        return False
    _reset_rate[username].append(now)
    return True