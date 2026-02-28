import os
import json
import jwt
from dotenv import load_dotenv
from flask import Flask, jsonify, g
from auth.blueprint import auth_bp
from auth.middleware import install_auth_middleware
from auth.user_management import create_user, get_user_by_username, delete_user
import db.functions.connect

load_dotenv()

# Configure auth to use test_auth database globally
# This is cleaner than monkey-patching specific modules
db.functions.connect.auth_db_config.update({
    'database': 'test_auth'
})

app = Flask(__name__)

# Configuration required by auth.tokens
app.config.update({
    "JWT_SECRET": os.getenv("JWT_SECRET", "demo-secret-key-change-me"),
    "JWT_ACCESS_TTL_SECONDS": int(os.getenv("JWT_ACCESS_TTL_SECONDS", 3600)),
    "JWT_ISSUER": os.getenv("JWT_ISSUER", "demo-issuer"),
    "JWT_AUDIENCE": os.getenv("JWT_AUDIENCE", "demo-audience"),
})

# 1. Register the Auth Blueprint (provides /auth/login)
app.register_blueprint(auth_bp, url_prefix="/auth")

# 2. Install Middleware (protects /api/* routes)
install_auth_middleware(app)

@app.route("/api/profile", methods=["GET", "POST"])
def profile():
    """
    A protected route. 
    If you can reach this, your Token is valid and Middleware is working.
    """
    return jsonify({
        "message": "Access granted",
        "user_id": g.user_id,
        "tenant_id": g.tenant_id,
        "status": "authenticated"
    })

def print_header(title):
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")

def print_response(response):
    print(f"HTTP {response.status_code}")
    try:
        print(json.dumps(response.get_json(), indent=2))
    except:
        print(response.data.decode('utf-8'))

def demo_jwt_flow():
    client = app.test_client()
    
    # Setup a demo user for testing
    username = "demo_simulation_user"
    password = "securePassword123!"
    email = "demo_sim@example.com"
    should_cleanup = False
    
    print("--- Setting up Demo User in DB ---")
    try:
        if not get_user_by_username(username):
            create_user(username, password, email, role="Admin")
            print(f"Created user: {username}")
            should_cleanup = True
        else:
            print(f"User {username} already exists")
            should_cleanup = True
    except Exception as e:
        print(f"Skipping DB setup (DB might be offline): {e}")
        return

    try:
        # 1. Unauthenticated Access
        print_header("1. Attempting Unauthenticated Access")
        print("Request: GET /api/profile")
        res = client.get("/api/profile")
        print_response(res)

        # 2. Login with Bad Credentials
        print_header("2. Login with Bad Credentials")
        print(f"Request: POST /auth/login (user={username}, pass=wrong)")
        res = client.post("/auth/login", json={"username": username, "password": "wrong"})
        print_response(res)

        # 3. Login with Good Credentials
        print_header("3. Login with Correct Credentials")
        print(f"Request: POST /auth/login (user={username}, pass={password})")
        res = client.post("/auth/login", json={"username": username, "password": password})
        print_response(res)
        
        if res.status_code != 200:
            print("Login failed, aborting demo.")
            return

        token = res.get_json().get("token")
        print(f"\n[Client] Received Token: {token[:15]}...{token[-15:]}")
        
        # Decode token to show structure (educational)
        try:
            # We use verify_signature=False here just to inspect the payload for the demo
            decoded = jwt.decode(token, options={"verify_signature": False})
            print(f"[Client] Token Payload: {decoded}")
        except Exception as e:
            print(f"[Client] Could not decode token for display: {e}")

        # 4. Authenticated Access
        print_header("4. Accessing Protected Route with Token")
        print("Request: GET /api/profile")
        print("Header: Authorization: Bearer <token>")
        res = client.get("/api/profile", headers={"Authorization": f"Bearer {token}"})
        print_response(res)

        # 5. Security Check: Tenant ID Injection (Query Param)
        print_header("5. Security Check: Spoof Tenant ID (Query Param)")
        print("Request: GET /api/profile?tenant_id=999")
        print("Header: Authorization: Bearer <token>")
        res = client.get("/api/profile?tenant_id=999", headers={"Authorization": f"Bearer {token}"})
        print_response(res)

        # 6. Security Check: Tenant ID Injection (JSON Body)
        print_header("6. Security Check: Spoof Tenant ID (JSON Body)")
        print("Request: POST /api/profile")
        print("Body: { 'tenant_id': 999 }")
        print("Header: Authorization: Bearer <token>")
        res = client.post("/api/profile", 
                          json={"tenant_id": 999, "some_data": "test"}, 
                          headers={"Authorization": f"Bearer {token}"})
        print_response(res)

    finally:
        if should_cleanup:
            print("\n--- Cleanup ---")
            try:
                user = get_user_by_username(username)
                if user:
                    delete_user(user['tenant_id'], user['user_id'])
                    print(f"Deleted user: {username}")
            except Exception as e:
                print(f"Error cleaning up user: {e}")

    print("\n--- Demo Complete ---")

if __name__ == "__main__":
    demo_jwt_flow()