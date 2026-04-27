import mysql.connector
import secrets
import string
from contextlib import contextmanager, closing
from typing import Optional, List, Dict, Any
from db.functions.connect import get_auth_db
from auth.passwords import hash_password

"""
Manages creation and deletion (not implemented on front end) of users in auth database.
"""

@contextmanager
def _get_db_context(conn=None):
    if conn:
        yield conn
    else:
        connection = get_auth_db()
        if connection is None:
            raise RuntimeError("Failed to connect to user database")
        try:
            yield connection
        finally:
            connection.close()


def _execute_proc(proc_name: str, args: List[Any], conn=None) -> List[Dict[str, Any]]:
    """
    Executes a stored procedure that returns rows (e.g., SELECT or DELETE returning info).
    """
    with _get_db_context(conn) as connection:
        with closing(connection.cursor(dictionary=True)) as cur:
            cur.callproc(proc_name, args)
            rows = []
            for r in cur.stored_results():
                rows.extend(r.fetchall())
            connection.commit()
            return rows


def _call_user_create_proc(proc_name: str, args: List[Any], conn=None) -> Optional[int]:
    """
    Executes a stored procedure on the USER database that inserts a record and returns its new ID.
    Handles connection lifecycle (opens/closes if conn is None).
    """
    new_id = None
    
    with _get_db_context(conn) as connection:
        try:
            with closing(connection.cursor()) as cur:
                cur.callproc(proc_name, args)

                for r in cur.stored_results():
                    row = r.fetchone()
                    if row:
                        new_id = row[0]
                connection.commit()
        except mysql.connector.errors.IntegrityError as e:
            if e.errno == 1062:
                raise ValueError("User already exists") from e
            raise

    return new_id


def create_user(username: str, password: str, email: str, role: str = "User", conn=None) -> Optional[int]:
    if not username:
        raise ValueError("Username is required")
    
    hashed_pw = hash_password(password)

    # Proc signature: add_user(p_tenant_id, p_username, p_password_hash, p_email, p_role)
    # Note: p_tenant_id is ignored by the proc in the current "User IS Tenant" model, passing 0.
    args = [0, username, hashed_pw, email, role]
    
    return _call_user_create_proc("add_user", args, conn)


def delete_user(tenant_id: int, user_id: int, conn=None) -> List[Dict[str, Any]]:
    """
    Deletes a user by ID from the user database.
    """
    if user_id is None:
        raise ValueError("User ID is required")
    
    return _execute_proc("delete_user", [tenant_id, user_id], conn)


def get_user_by_username(username: str, conn=None) -> Optional[Dict[str, Any]]:
    rows = _execute_proc("get_user_by_username", [username], conn)
    return rows[0] if rows else None


def get_user_totp_secret(user_id):
    rows = _execute_proc("get_user_totp", [user_id])
    return rows[0]["totp_secret"] if rows else None


def set_totp_secret(user_id, secret):
    _execute_proc("set_totp_secret", [user_id, secret])


def set_totp_confirmed(user_id, confirmed):
    _execute_proc("set_totp_confirmed", [user_id, confirmed])


def get_user_for_reset(username):
    rows = _execute_proc("get_user_for_reset", [username])
    return rows[0] if rows else None


def update_user_password(user_id, password_hash):
    _execute_proc("update_user_password", [user_id, password_hash])


def get_user_totp(user_id):
    rows = _execute_proc("get_user_totp", [user_id])
    return rows[0] if rows else None


def generate_username(length=12):
    username = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(length))
    return username


def generate_password(length=16):
    password = string.ascii_letters + string.digits + "!@#$%^&*-_=+"
    password = ''.join(secrets.choice(password) for _ in range(length))
    return password


def generate_email(username):
    return f"{username}@example.invalid"


def create_anonymous_user(conn=None):
    password = generate_password()
    username = generate_username()
    email = generate_email(username)
    user_id = create_user(username,  password, email, role="Anonymous", conn=conn)
    user = get_user_by_username(username, conn=conn)
    return user_id, user["tenant_id"]


def update_user_activity(user_id, conn = None):
    _execute_proc("update_user_activity", [user_id], conn)


def upgrade_anonymous_user(user_id, username, email, password, conn=None):
    hashed_pw = hash_password(password)
    _execute_proc("upgrade_anonymous_user", [user_id, username, email, hashed_pw], conn)
