from dotenv import load_dotenv
import mysql.connector
from mysql.connector import pooling
import os

load_dotenv()

db_config = {
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT"),
    "database": os.getenv("DB_NAME"),
    "connection_timeout": 10,
    "use_pure": True
}

auth_db_config = {
    "user": os.getenv("AUTH_DB_USER"),
    "password": os.getenv("AUTH_DB_PASSWORD"),
    "host": os.getenv("AUTH_DB_HOST"),
    "port": os.getenv("AUTH_DB_PORT"),
    "database": os.getenv("AUTH_DB_NAME"),
    "connection_timeout": 10,
    "use_pure": True
}

# Global pools
_db_pool = None
_auth_db_pool = None


def get_db():
    global _db_pool
    try:
        if _db_pool is None:
            _db_pool = pooling.MySQLConnectionPool(
                pool_name="main_pool",
                pool_size=5,
                **db_config
            )
        return _db_pool.get_connection()
    except Exception as e:
        # Security: Don't print full exception as it may contain credentials
        print(f"DB Connection Error: {type(e).__name__}")
        return None


def get_auth_db():
    global _auth_db_pool
    try:
        if _auth_db_pool is None:
            _auth_db_pool = pooling.MySQLConnectionPool(
                pool_name="auth_pool",
                pool_size=5,
                **auth_db_config
            )
        return _auth_db_pool.get_connection()
    except Exception as e:
        # Security: Don't print full exception as it may contain credentials
        print(f"User DB Connection Error: {type(e).__name__}")
        return None
