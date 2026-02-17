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

auth_db_config = {
    "user": os.getenv("AUTH_DB_USER"),
    "password": os.getenv("AUTH_DB_PASSWORD"),
    "host": os.getenv("AUTH_DB_HOST"),
    "port": os.getenv("AUTH_DB_PORT"),
    "database": os.getenv("AUTH_DB_NAME"),
    "connection_timeout": 10
}


def get_db():
    try:
        return mysql.connector.connect(**db_config)
    except Exception as e:
        # Security: Don't print full exception as it may contain credentials
        print(f"DB Connection Error: {type(e).__name__}")
        return None


def get_auth_db():
    try:
        return mysql.connector.connect(**auth_db_config)
    except Exception as e:
        # Security: Don't print full exception as it may contain credentials
        print(f"User DB Connection Error: {type(e).__name__}")
        return None
