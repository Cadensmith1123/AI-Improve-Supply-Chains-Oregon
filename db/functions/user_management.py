from db.functions.connect import get_auth_db


def _call_user_create_proc(proc_name, args, conn=None):
    """
    Executes a stored procedure on the USER database that inserts a record and returns its new ID.
    Handles connection lifecycle (opens/closes if conn is None).
    """
    should_close = False
    if conn is None:
        conn = get_auth_db()
        should_close = True
    
    if conn is None:
        raise RuntimeError("Failed to connect to user database")

    new_id = None
    try:
        cur = conn.cursor()
        cur.callproc(proc_name, args)

        for r in cur.stored_results():
            row = r.fetchone()
            if row:
                new_id = row[0]
        conn.commit()
        cur.close()
    finally:
        if should_close and conn:
            conn.close()

    return new_id


def create_user(username, password, email, tenant_id=0, role="User", conn=None):
    """
    Creates a new user with a hashed password in the user database.
    """
    if not username:
        raise ValueError("username is required")
    
    from auth.passwords import hash_password
    # hash_password handles validation (not None, min length)
    hashed_pw = hash_password(password)

    # args for add_user(p_tenant_id, p_username, p_password_hash, p_email, p_role)
    args = [tenant_id or 0, username, hashed_pw, email, role]
    
    return _call_user_create_proc("add_user", args, conn)


def delete_user(tenant_id, user_id, conn=None):
    """
    Deletes a user by ID from the user database.
    """
    if user_id is None:
        raise ValueError("user_id is required")

    should_close = False
    if conn is None:
        conn = get_auth_db()
        should_close = True
    
    if conn is None:
        raise RuntimeError("Failed to connect to user database")

    try:
        cur = conn.cursor(dictionary=True)
        cur.callproc("delete_user", [tenant_id, user_id])
        
        rows = []
        for r in cur.stored_results():
            rows.extend(r.fetchall())
            
        conn.commit()
        cur.close()
        return rows
    finally:
        if should_close and conn:
            conn.close()


def get_user_by_username(username, conn=None):
    should_close = False
    if conn is None:
        conn = get_auth_db()
        should_close = True
    
    if conn is None:
        return None

    try:
        cur = conn.cursor(dictionary=True)
        # Assuming table 'users' exists
        cur.execute("SELECT user_id, tenant_id, password_hash, role FROM users WHERE username = %s", (username,))
        return cur.fetchone()
    finally:
        if should_close and conn:
            conn.close()