import os
import re
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

# List of SQL files to execute in order
SQL_FILES = [
    "db/schema/SCHEMA.sql",
    "db/procedures/create_procs.sql",
    "db/procedures/read_procs.sql",
    "db/procedures/update_procs.sql",
    "db/procedures/delete_procs.sql",
    "db/procedures/create_trip_header.sql",
    "db/procedures/update_trip_header.sql",
    "db/procedures/get_trip_details.sql",
    "db/procedures/get_planning_assets.sql",
    "db/procedures/generate_test_data.sql"
]

def get_db_connection():
    return mysql.connector.connect(
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        database=os.getenv("DB_NAME", "local_food_db") # Default to local_food_db if not set
    )

def execute_sql_file(conn, file_path):
    print(f"Executing {file_path}...")
    with open(file_path, 'r') as f:
        sql_script = f.read()

    # Split file into segments based on 'DELIMITER $$'
    # Segment 0 is standard SQL (; separated)
    # Segments 1+ are compound SQL ($$ separated)
    segments = sql_script.split('DELIMITER $$')
    
    # Use a fresh buffered cursor for each file to avoid sync issues
    cursor = conn.cursor(buffered=True)
    
    try:
        # Process Segment 0 (Standard SQL)
        standard_part = segments[0]
        statements = [s.strip() for s in standard_part.split(';') if s.strip()]
        
        # Process Segments 1+ (Compound SQL)
        for segment in segments[1:]:
            # Remove the trailing 'DELIMITER ;' if present
            segment = re.sub(r"DELIMITER\s+;\s*$", "", segment, flags=re.IGNORECASE | re.MULTILINE)
            # Split by $$
            compound_parts = [s.strip() for s in segment.split('$$') if s.strip()]
            statements.extend(compound_parts)
            
        for statement in statements:
            try:
                cursor.execute(statement)
                
                # Robustly consume all results
                while True:
                    if cursor.with_rows:
                        cursor.fetchall()
                    if not cursor.nextset():
                        break
                    
            except mysql.connector.Error as err:
                print(f"Error executing statement in {file_path}: {err}")
                print(f"Statement start: {statement[:100]}...")
    finally:
        cursor.close()

def main():
    try:
        conn = get_db_connection()
        
        for file_path in SQL_FILES:
            if os.path.exists(file_path):
                execute_sql_file(conn, file_path)
            else:
                print(f"Warning: File not found {file_path}")
        
        conn.commit()
        print("Database rebuild complete.")
        
    except mysql.connector.Error as err:
        print(f"Database connection error: {err}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            conn.close()

if __name__ == "__main__":
    main()
