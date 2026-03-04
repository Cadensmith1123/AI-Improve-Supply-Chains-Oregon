import sys
import os
import jwt
from flask import Flask, render_template, request, redirect, url_for, g, make_response
from dotenv import load_dotenv

# Add parent directory to path so we can import 'db' package
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

"""
Entry point into the application
"""

import access_db as db
from map_route import map_bp
from routes_bp import routes_bp
from products_bp import products_bp
from assets_bp import assets_bp
from auth.blueprint import auth_bp
from auth.tokens import verify_access_token

load_dotenv()

app = Flask(__name__)
app.config.update({
    'JWT_SECRET': os.getenv("JWT_SECRET", "dev-secret-key"),
    'JWT_ACCESS_TTL_SECONDS': int(os.getenv("JWT_ACCESS_TTL_SECONDS", 3600)),
    'JWT_ISSUER': os.getenv("JWT_ISSUER", "local-food-app"),
    'JWT_AUDIENCE': os.getenv("JWT_AUDIENCE", "local-food-api")
})

# Register Blueprints
app.register_blueprint(map_bp)
app.register_blueprint(routes_bp)
app.register_blueprint(products_bp)
app.register_blueprint(assets_bp)
app.register_blueprint(auth_bp, url_prefix="/auth")

@app.before_request
def load_user_from_token():
    """Middleware to authenticate users via JWT in cookie."""
    # Allow public endpoints
    if request.endpoint in ['static', 'auth.login', 'auth.register', 'health', 'logout']:
        return

    # Get Token from Cookie
    token = request.cookies.get('token')
    
    if not token:
        return redirect(url_for('auth.login'))

    # Verify Token
    try:
        payload = verify_access_token(token)
        g.user_id = payload.get('sub')
        g.tenant_id = payload.get('tid')
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return redirect(url_for('logout'))

@app.get("/health")
def health():
    return {"status": "ok"}

@app.route('/logout')
def logout():
    resp = make_response(redirect(url_for('auth.login')))
    resp.delete_cookie('token')
    return resp

@app.get("/")
def home():
    return redirect(url_for("routes.routes_list"))


if __name__ == "__main__":
    app.run(debug=True)
