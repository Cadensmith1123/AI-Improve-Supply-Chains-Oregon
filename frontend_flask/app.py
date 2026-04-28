import sys
import os
from flask import Flask, redirect, url_for, make_response
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
from auth_bp import auth_bp
from auth.middleware import install_auth_middleware

load_dotenv()

app = Flask(__name__)
app.config.update({
    'JWT_SECRET': os.getenv("JWT_SECRET", "dev-secret-key"),
    'JWT_ACCESS_TTL_SECONDS': int(os.getenv("JWT_ACCESS_TTL_SECONDS", 3600)),
    'JWT_ISSUER': os.getenv("JWT_ISSUER", "local-food-app"),
    'JWT_AUDIENCE': os.getenv("JWT_AUDIENCE", "local-food-api"),
    'SECRET_KEY': os.getenv("SECRET_KEY", "dev-secret-key"),
    'ANON_RECOVERY_TTL_SECONDS': int(os.getenv("ANON_RECOVERY_TTL_SECONDS", 7 * 24 * 3600))
})

# Register Blueprints
app.register_blueprint(map_bp)
app.register_blueprint(routes_bp)
app.register_blueprint(products_bp)
app.register_blueprint(assets_bp)
app.register_blueprint(auth_bp, url_prefix="/auth")

# Install Auth Middleware
install_auth_middleware(app)

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
