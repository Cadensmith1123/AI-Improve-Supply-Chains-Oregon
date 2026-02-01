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

