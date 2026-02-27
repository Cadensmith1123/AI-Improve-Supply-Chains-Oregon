import mysql.connector
from contextlib import contextmanager, closing
from typing import Optional, List, Dict, Any
from db.functions.connect import get_auth_db
from auth.passwords import hash_password


@contextmanager
def _get_db_context(conn=None):
    """
    Context manager to handle database connection lifecycle.
    Uses provided connection or creates a new one.
    Closes the connection only if it was created within this context.
    """
    if conn:
        yield conn
        return

    conn = get_auth_db()
    if conn is None:
        raise RuntimeError("Failed to connect to user database")

    try:
        yield conn
    finally:
        conn.close()


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


def create_user(username: str, password: str, email: str, tenant_id: int = 0, role: str = "User", conn=None) -> Optional[int]:
    """
    Creates a new user with a hashed password in the user database.
    """
    if not username:
        raise ValueError("username is required")
    
    # hash_password handles validation (not None, min length)
    hashed_pw = hash_password(password)

    # args for add_user(p_tenant_id, p_username, p_password_hash, p_email, p_role)
    args = [tenant_id or 0, username, hashed_pw, email, role]
    
    return _call_user_create_proc("add_user", args, conn)


def delete_user(tenant_id: int, user_id: int, conn=None) -> List[Dict[str, Any]]:
    """
    Deletes a user by ID from the user database.
    """
    if user_id is None:
        raise ValueError("user_id is required")
    
    return _execute_proc("delete_user", [tenant_id, user_id], conn)


def get_user_by_username(username: str, conn=None) -> Optional[Dict[str, Any]]:
    """
    Retrieves a user record by username.
    """
    with _get_db_context(conn) as connection:
        with closing(connection.cursor(dictionary=True)) as cur:
            # Direct table access used here for simplicity; consider moving to a stored procedure (e.g., get_user_by_username)
            # to maintain consistency with the stored procedure pattern used elsewhere.
            query = "SELECT user_id, tenant_id, password_hash, role FROM users WHERE username = %s"
            cur.execute(query, (username,))
            return cur.fetchone()