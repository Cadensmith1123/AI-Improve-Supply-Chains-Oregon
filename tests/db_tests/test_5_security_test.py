import pytest
from unittest.mock import patch
from flask import Flask, g
import os
import mysql.connector
import dotenv

import db.functions.simple_functions.read as read
import db.functions.tennant_functions.scoped_read as scoped_read
import db.functions.tennant_functions.scoped_create as scoped_create

dotenv.load_dotenv()

def connect_db():
    try:
        config = {
            'user': os.getenv("DB_USER"),
            'password': os.getenv("DB_PASSWORD"),
            'host': os.getenv("DB_HOST"),
            'port': os.getenv("DB_PORT"),
            'database': 'test_db',
            'connection_timeout': 10
        }
        return mysql.connector.connect(**config)
    except Exception:
        return None

@pytest.fixture(scope="session")
def connection():
    conn = connect_db()
    yield conn
    if conn:
        conn.close()

def test_sql_injection_ids_arg(connection):
    """
    Attempt to inject SQL via the 'ids' parameter in read functions.
    The _ids_arg function should escape quotes to prevent breaking out of the IN clause.
    """

    malicious_id = "99999' OR '1'='1"

    rows = read.view_locations(tenant_id=1, conn=connection, ids=[malicious_id])
    assert len(rows) == 0

def test_sql_injection_backslash(connection):
    """
    Attempt to use backslash to escape the closing quote.
    Payload: \
    If vulnerable: ... IN ('\') ... (syntax error or eats next quote)
    If secure: ... IN ('\\') ... (literal backslash)
    """
    malicious_id = "\\"
    
    # Should run without syntax error and return nothing
    rows = read.view_locations(tenant_id=1, conn=connection, ids=[malicious_id])
    assert len(rows) == 0

def test_scoped_access_without_context():
    """
    Verify that scoped functions raise RuntimeError if g.tenant_id is missing.
    This ensures that functions cannot be called outside of an authenticated request context.
    """
    app = Flask(__name__)
    
    with app.app_context():
        # g.tenant_id is not set
        
        with pytest.raises(RuntimeError) as excinfo:
            scoped_read.view_locations_scoped()
        assert "Missing g.tenant_id" in str(excinfo.value)

        with pytest.raises(RuntimeError) as excinfo:
            scoped_create.add_location_scoped(name="Test", type="Hub")
        assert "Missing g.tenant_id" in str(excinfo.value)

def test_scoped_access_with_context():
    """
    Verify that scoped functions work correctly when g.tenant_id is set.
    We mock the underlying simple function to avoid needing a real DB connection for this logic test.
    """
    app = Flask(__name__)
    
    with app.app_context():
        g.tenant_id = 123
        
        # Patch the underlying simple function to verify it gets called with the tenant_id from g
        with patch('db.functions.tennant_functions.scoped_read.view_locations') as mock_view:
            scoped_read.view_locations_scoped(limit=5)
            
            mock_view.assert_called_once()
            args, kwargs = mock_view.call_args
            assert args[0] == 123 # tenant_id passed from g
            assert kwargs['limit'] == 5