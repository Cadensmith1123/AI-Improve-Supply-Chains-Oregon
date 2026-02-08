import pytest
import os
import sys
import mysql.connector
import dotenv
import re

dotenv.load_dotenv()

# List of SQL files to execute in order
SQL_FILES = [
    r"db/schema/SCHEMA.sql",
    r"db/procedures/create_procs.sql",
    r"db/procedures/read_procs.sql",
    r"db/procedures/update_procs.sql",
    r"db/procedures/delete_procs.sql",
    r"db/procedures/create_trip_header.sql",
    r"db/procedures/update_trip_header.sql",
    r"db/procedures/get_trip_details.sql",
    r"db/procedures/get_planning_assets.sql",
    r"db/procedures/generate_test_data.sql"
]

def create_test_db():
    try:
        config = {
            'user': os.getenv("DB_USER"),
            'password': os.getenv("DB_PASSWORD"),
            'host': os.getenv("DB_HOST"),
            'port': os.getenv("DB_PORT"),
            'connection_timeout': 10
        }
        # Create new test DB
        connection = mysql.connector.connect(**config)
        cursor = connection.cursor()
        cursor.execute(f"DROP DATABASE IF EXISTS test_db")
        cursor.execute(f"CREATE DATABASE test_db")
        connection.close()

        # return connection to test_db
        config['database'] = 'test_db'
        connection = mysql.connector.connect(**config)

        return connection
    except Exception as e:
        print(f"DB Error: {e}")
        return None


def execute_sql_script(connection, file_path):
    cursor = connection.cursor()
    statement_count = 0

    try:
        with open(file_path, 'r') as file:
            sql_script = file.read()

            # Sanitization
            sql_script = re.sub(r"(DROP SCHEMA IF EXISTS|CREATE SCHEMA|USE|CALL)\s+local_food_db;", 
                                r"-- \1 local_food_db;", 
                                sql_script, flags=re.IGNORECASE)

            # Clean delimiters
            sql_script = re.sub(r"DELIMITER\s+\S+", "", sql_script, flags=re.IGNORECASE)
            sql_script = sql_script.replace("$$", ";")

            results = cursor.execute(sql_script, multi=True)

            for result in results:
                statement_count += 1
                if result.with_rows:
                    result.fetchall()

            cursor.close()
            connection.commit()
            return statement_count/2

    except Exception as e:
        print(f"Failed to create procedure: {e}")
        raise   


@pytest.fixture(scope="session")
def connection():
    conn = create_test_db()
    yield conn
    if conn:
        conn.close()


def get_db_proc_count(connection):
    """Helper to get current procedure count"""
    cursor = connection.cursor()
    cursor.execute("SHOW PROCEDURE STATUS WHERE Db = 'test_db'")
    return len(cursor.fetchall())


def test_01_database_creation(connection):
    assert connection is not None
    assert connection.is_connected()
    cursor = connection.cursor()
    cursor.execute("SELECT DATABASE()")
    current_db = cursor.fetchone()[0]
    assert current_db == "test_db"


def test_02_schema_creation(connection):
    execute_sql_script(connection, SQL_FILES[0])
    cursor = connection.cursor()
    cursor.execute("SHOW TABLES")
    tables = cursor.fetchall()
    assert len(tables) > 0


def test_03_create_procs(connection):
    # 1. Snapshot BEFORE
    count_before = get_db_proc_count(connection)
    
    # 2. Run Script
    statement_count = execute_sql_script(connection, SQL_FILES[1])
    
    # 3. Snapshot AFTER
    count_after = get_db_proc_count(connection)
    
    # 4. Verify: Increase in DB matches statements in file
    assert statement_count == (count_after - count_before)


def test_04_read_procs(connection):
    count_before = get_db_proc_count(connection)
    statement_count = execute_sql_script(connection, SQL_FILES[2])
    count_after = get_db_proc_count(connection)
    assert statement_count == (count_after - count_before)


def test_05_update_procs(connection):
    count_before = get_db_proc_count(connection)
    statement_count = execute_sql_script(connection, SQL_FILES[3])
    count_after = get_db_proc_count(connection)
    assert statement_count == (count_after - count_before)


def test_06_delete_procs(connection):
    count_before = get_db_proc_count(connection)
    statement_count = execute_sql_script(connection, SQL_FILES[4])
    count_after = get_db_proc_count(connection)
    assert statement_count == (count_after - count_before)


def test_07_create_trip_header(connection):
    count_before = get_db_proc_count(connection)
    statement_count = execute_sql_script(connection, SQL_FILES[5])
    count_after = get_db_proc_count(connection)
    assert statement_count == (count_after - count_before)


def test_08_update_trip_header(connection):
    count_before = get_db_proc_count(connection)
    statement_count = execute_sql_script(connection, SQL_FILES[6])
    count_after = get_db_proc_count(connection)
    assert statement_count == (count_after - count_before)


def test_09_get_trip_details(connection):
    count_before = get_db_proc_count(connection)
    statement_count = execute_sql_script(connection, SQL_FILES[7])
    count_after = get_db_proc_count(connection)
    assert statement_count == (count_after - count_before)


def test_10_get_planning_assets(connection):
    count_before = get_db_proc_count(connection)
    statement_count = execute_sql_script(connection, SQL_FILES[8])
    count_after = get_db_proc_count(connection)
    assert statement_count == (count_after - count_before)


def test_11_generate_test_data(connection):
    count_before = get_db_proc_count(connection)
    statement_count = execute_sql_script(connection, SQL_FILES[9])
    count_after = get_db_proc_count(connection)
    
    
    assert statement_count/2 == (count_after - count_before)
