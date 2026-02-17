from dotenv import load_dotenv
import mysql.connector
import os

load_dotenv()

db_config = {
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT"),
    "database": os.getenv("DB_NAME"),
    "connection_timeout": 10

}


def get_db():
    try:
        return mysql.connector.connect(**db_config)
    except Exception as e:
        print(f"DB Error: {e}")
        return None


def execute_creation_proc(proc_name, args, conn=None):
    """
    Executes a stored procedure that inserts a record and returns its new ID.
    Handles connection lifecycle (opens/closes if conn is None).
    """
    should_close = False
    if conn is None:
        conn = get_db()
        should_close = True

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
