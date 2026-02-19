import os
import mysql.connector
from flask import Flask, request, jsonify
from dotenv import load_dotenv
import re

# DB Functions
from auth import user_management
from db.functions.tennant_functions import scoped_create, scoped_read, scoped_delete
import db.functions.connect

# Auth Initialization
from auth.init import init_auth

load_dotenv()

def connect_test_db():
    try:
        config = {
            'user': os.getenv("DB_USER"),
            'password': os.getenv("DB_PASSWORD"),
            'host': os.getenv("DB_HOST"),
            'port': os.getenv("DB_PORT"),
            'database': 'test_db',
            'connection_timeout': 10
        }
        return mysql.connector.connect(**config)
    except Exception as e:
        print(f"Test DB Connection failed: {e}")
        return None

def execute_sql_file(cursor, file_path):
    with open(file_path, 'r') as f:
        sql_script = f.read()
        
        # Sanitize: Remove database creation/switching to ensure we stay in test_auth
        sql_script = re.sub(r"(DROP SCHEMA IF EXISTS|CREATE SCHEMA|CREATE DATABASE|USE)\s+\w+;", "", sql_script, flags=re.IGNORECASE)
        
        # Handle Delimiters for Procedures (convert $$ to ; and remove DELIMITER statements)
        sql_script = re.sub(r"DELIMITER\s+\S+", "", sql_script, flags=re.IGNORECASE)
        sql_script = sql_script.replace("$$", ";")
        
        # Execute statements using multi=True to handle the script
        for result in cursor.execute(sql_script, multi=True):
            if result.with_rows:
                result.fetchall()

def setup_test_auth_db():
    """Rebuilds the test_auth database from schema files to ensure it is fresh."""
    print("Rebuilding test_auth database...")
    conn = mysql.connector.connect(
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT")
    )
    cursor = conn.cursor()
    
    cursor.execute("DROP DATABASE IF EXISTS test_auth")
    cursor.execute("CREATE DATABASE test_auth")
    cursor.execute("USE test_auth")
    
    # Execute Schema and Procs
    execute_sql_file(cursor, "db/schema/auth_SCHEMA.sql")
    execute_sql_file(cursor, "db/procedures/auth_procs.sql")
    
    conn.commit()
    cursor.close()
    conn.close()
    print("test_auth database ready.")

def run_demo():
    # 0. Ensure Test DB is Fresh
    setup_test_auth_db()

    # Patch the auth db config to use the test database for this demo
    # This ensures the Flask app connects to the same DB we are setting up here
    db.functions.connect.auth_db_config.update({
        'user': os.getenv("DB_USER"),
        'password': os.getenv("DB_PASSWORD"),
        'host': os.getenv("DB_HOST"),
        'port': os.getenv("DB_PORT"),
        'database': 'test_auth'
    })

    # 1. Setup Flask App (The Server)
    app = Flask(__name__)
    app.config["JWT_SECRET"] = os.getenv("JWT_SECRET", "dev-secret-key")
    app.config["JWT_ISSUER"] = os.getenv("JWT_ISSUER", "local-food-app")
    app.config["JWT_AUDIENCE"] = os.getenv("JWT_AUDIENCE", "local-food-api")
    app.config["JWT_ACCESS_TTL_SECONDS"] = 3600

    # 2. Initialize Auth (Registers Blueprint & Middleware)
    # This installs the logic that intercepts requests and checks for tokens
    init_auth(app)

    # 3. Define API Routes (Simulating your Backend Endpoints)
    # These routes don't need to check auth manually; middleware does it.
    @app.route("/api/locations", methods=["POST"])
    def create_location():
        # Middleware has already run: g.tenant_id is set securely
        data = request.get_json()
        conn = connect_test_db()
        try:
            loc_id = scoped_create.add_location_scoped(
                name=data["name"],
                type=data["type"],
                address_street=data.get("address"),
                city=data.get("city"),
                state=data.get("state"),
                zip_code=data.get("zip"),
                conn=conn
            )
            return jsonify({"location_id": loc_id}), 201
        finally:
            if conn: conn.close()

    @app.route("/api/locations/<int:loc_id>", methods=["GET"])
    def get_location(loc_id):
        conn = connect_test_db()
        try:
            # scoped_read checks g.tenant_id internally
            locs = scoped_read.view_locations_scoped(ids=[loc_id], conn=conn)
            if not locs:
                return jsonify({"error": "Not found"}), 404
            return jsonify(locs[0])
        finally:
            if conn: conn.close()

    @app.route("/api/locations/<int:loc_id>", methods=["DELETE"])
    def delete_location(loc_id):
        conn = connect_test_db()
        try:
            scoped_delete.delete_location_scoped(location_id=loc_id, conn=conn)
            return jsonify({"status": "deleted"}), 200
        finally:
            if conn: conn.close()

    # 4. Setup Demo Data (User)
    tenant_id = None # Will be assigned upon creation
    username = "jwt_demo_user"
    password = "SecurePassword123!"
    email = "jwt_demo@example.com"
    user_id = None

    try:
        print("\n=== 1. Setup: Register User in DB ===")
        # We pass conn=None to let user_management use the patched global config
        existing_user = user_management.get_user_by_username(username, conn=None)
        if existing_user:
            user_management.delete_user(existing_user['tenant_id'], existing_user['user_id'], conn=None)
        
        user_id = user_management.create_user(username, password, email, conn=None)
        
        # Fetch the assigned tenant_id for cleanup later
        created_user = user_management.get_user_by_username(username, conn=None)
        tenant_id = created_user['tenant_id']
        
        print(f"User created with ID: {user_id}, Tenant ID: {tenant_id}")

        # 5. Simulate Browser Interaction
        client = app.test_client()

        print("\n=== 2. Browser: Login (POST /auth/login) ===")
        # We send credentials, server verifies and returns JWT
        login_resp = client.post("/auth/login", json={
            "username": username,
            "password": password
        })
        
        if login_resp.status_code != 200:
            print(f"Login Failed: {login_resp.json}")
            return

        token = login_resp.json.get("token")
        print(f"Received JWT: {token[:30]}...")

        print("\n=== 3. Browser: Create Location (POST /api/locations) ===")
        # We attach the token to the Authorization header
        headers = {"Authorization": f"Bearer {token}"}
        
        create_resp = client.post("/api/locations", json={
            "name": "JWT Secure Hub",
            "type": "Hub",
            "address": "123 Web Way",
            "city": "Internet City",
            "state": "OR",
            "zip": "99999"
        }, headers=headers)

        if create_resp.status_code == 201:
            loc_id = create_resp.json["location_id"]
            print(f"Location created successfully via API. ID: {loc_id}")
        else:
            print(f"Create Failed: {create_resp.status_code} - {create_resp.json}")
            return

        print("\n=== 4. Browser: Read Location (GET /api/locations/<id>) ===")
        # Middleware intercepts, verifies token, sets g.tenant_id, scoped_read uses it
        read_resp = client.get(f"/api/locations/{loc_id}", headers=headers)
        print(f"Read Response: {read_resp.json}")

        print("\n=== 5. Browser: Delete Location (DELETE /api/locations/<id>) ===")
        del_resp = client.delete(f"/api/locations/{loc_id}", headers=headers)
        print(f"Delete Status: {del_resp.status_code}")

        # Verify deletion
        verify_resp = client.get(f"/api/locations/{loc_id}", headers=headers)
        if verify_resp.status_code == 404:
            print("Verification: Location is gone.")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\n=== Cleanup ===")
        if user_id and tenant_id:
            user_management.delete_user(tenant_id, user_id, conn=None)

if __name__ == "__main__":
    run_demo()