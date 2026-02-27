# app.py
import sys
import os

# Add parent directory to path so we can import 'db' package
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Flask, render_template, request, redirect, url_for, abort, jsonify, g, make_response
import jwt
from dotenv import load_dotenv
import access_db as db
# import blueprint
from map_route import map_bp
from routes_bp import routes_bp
from products_bp import products_bp
from assets_bp import assets_bp
from auth.blueprint import auth_bp
from auth.tokens import verify_access_token

load_dotenv()

app = Flask(__name__)
app.config['JWT_SECRET'] = os.getenv("JWT_SECRET", "dev-secret-key")
app.config['JWT_ACCESS_TTL_SECONDS'] = int(os.getenv("JWT_ACCESS_TTL_SECONDS", 3600))
app.config['JWT_ISSUER'] = os.getenv("JWT_ISSUER", "local-food-app")
app.config['JWT_AUDIENCE'] = os.getenv("JWT_AUDIENCE", "local-food-api")

# register the blueprint
app.register_blueprint(map_bp)
app.register_blueprint(routes_bp)
app.register_blueprint(products_bp)
app.register_blueprint(assets_bp)
app.register_blueprint(auth_bp, url_prefix="/auth")

@app.before_request
def load_user_from_token():
    """
    Checks for a 'token' cookie on every request.
    If valid, sets g.user_id and g.tenant_id.
    If invalid/missing, redirects to /login (unless it's a public endpoint).
    """
    # 1. Allow public endpoints (Login page, Static files, Auth API)
    if request.endpoint in ['login_page', 'register_page', 'static', 'auth.login', 'auth.register', 'health', 'logout']:
        return

    # 2. Get Token from Cookie
    token = request.cookies.get('token')
    
    if not token:
        return redirect(url_for('login_page'))

    # 3. Verify Token
    try:
        payload = verify_access_token(token)
        g.user_id = payload.get('sub')
        g.tenant_id = payload.get('tid')
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        # Token is bad - force logout/redirect
        return redirect(url_for('logout'))

@app.get("/health")
def health():
    return {"status": "ok"}

@app.route('/login')
def login_page():
    # If already logged in, redirect to dashboard
    if request.cookies.get('token'):
        try:
            verify_access_token(request.cookies.get('token'))
            return redirect(url_for('home'))
        except:
            pass
    return render_template('login.html')

@app.route('/register')
def register_page():
    # If already logged in, redirect to dashboard
    if request.cookies.get('token'):
        return redirect(url_for('home'))
    return render_template('register.html')

@app.route('/logout')
def logout():
    # Clear the cookie and redirect to login
    resp = make_response(redirect(url_for('login_page')))
    resp.delete_cookie('token')
    return resp

@app.get("/")
def home():
    return redirect(url_for("routes.routes_list"))


if __name__ == "__main__":
    app.run(debug=True)
