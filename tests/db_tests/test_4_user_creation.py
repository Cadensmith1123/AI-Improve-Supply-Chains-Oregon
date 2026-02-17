import pytest
import os
import mysql.connector
import dotenv
from db.functions import user_management

dotenv.load_dotenv()

def connect_auth_db():
    try:
        config = {
            'user': os.getenv("DB_USER"),
            'password': os.getenv("DB_PASSWORD"),
            'host': os.getenv("DB_HOST"),
            'port': os.getenv("DB_PORT"),
            'database': 'test_auth',
            'connection_timeout': 10
        }
        if not config['user']:
            return None
            
        return mysql.connector.connect(**config)
    except Exception:
        return None

@pytest.fixture(scope="session")
def auth_connection():
    conn = connect_auth_db()
    if not conn:
        pytest.skip("Auth DB connection failed or not configured. Skipping user tests.")
    yield conn
    conn.close()

def test_create_and_delete_user(auth_connection):
    username = "test_user_pytest"
    password = "securePassword123!"
    email = "test@example.com"
    role = "Admin"
    
    # 1. Create User
    # This calls the add_user stored procedure in the auth database
    user_id = user_management.create_user(
        username=username,
        password=password,
        email=email,
        role="Admin",
        conn=auth_connection
    )
    assert user_id is not None
    
    # 2. Verify in DB (Direct query since we don't have a public read_user function)
    cursor = auth_connection.cursor(dictionary=True)
    # Assuming standard table name 'users' and PK 'user_id' based on typical schema
    cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
    user_row = cursor.fetchone()
    cursor.close()
    
    assert user_row is not None
    assert user_row['username'] == username
    assert user_row['email'] == email
    assert user_row['role'] == "Admin"
    # Verify password is hashed (not plain text)
    assert user_row['password_hash'] != password
    assert len(user_row['password_hash']) > 20
    user_id = None
    try:
        # 1. Create User
        user_id = user_management.create_user(
            username=username,
            password=password,
            email=email,
            role=role,
            conn=auth_connection
        )
        assert user_id is not None
        
        # 2. Verify in DB
        cursor = auth_connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
        user_row = cursor.fetchone()
        cursor.close()
        
        assert user_row is not None
        assert user_row['username'] == username
        assert user_row['email'] == email
        assert user_row['role'] == role
        assert user_row['password_hash'] != password
        
        # 3. Delete User
        real_tenant_id = user_row['tenant_id']
        user_management.delete_user(real_tenant_id, user_id, conn=auth_connection)
        
        # 4. Verify Deletion
        cursor = auth_connection.cursor()
        cursor.execute("SELECT count(*) FROM users WHERE user_id = %s", (user_id,))
        count = cursor.fetchone()[0]
        cursor.close()
        assert count == 0
        user_id = None # Prevent cleanup from trying to delete again
        
    finally:
        if user_id:
            try:
                cursor = auth_connection.cursor(dictionary=True)
                cursor.execute("SELECT tenant_id FROM users WHERE user_id = %s", (user_id,))
                row = cursor.fetchone()
                cursor.close()
                if row:
                    user_management.delete_user(row['tenant_id'], user_id, conn=auth_connection)
            except Exception:
                pass

    # Get the real tenant_id assigned by the DB
    real_tenant_id = user_row['tenant_id']

    # 3. Delete User
    user_management.delete_user(real_tenant_id, user_id, conn=auth_connection)
    
    # 4. Verify Deletion
    cursor = auth_connection.cursor()
    cursor.execute("SELECT count(*) FROM users WHERE user_id = %s", (user_id,))
    count = cursor.fetchone()[0]
    cursor.close()
    assert count == 0

def test_create_user_validation(auth_connection):
    # Test missing username
    with pytest.raises(ValueError):
        user_management.create_user("", "pass", "email", conn=auth_connection)
        
    # Test weak password (validation handled by auth.passwords)
    with pytest.raises(ValueError):
        user_management.create_user("user", "short", "email", conn=auth_connection)