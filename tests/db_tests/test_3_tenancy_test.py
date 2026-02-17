import pytest
import os
import mysql.connector
import dotenv
from decimal import Decimal
from mysql.connector import errors as mysql_errors

import db.functions.simple_functions.read as read
import db.functions.simple_functions.create as create
import db.functions.simple_functions.delete as delete
import db.functions.scenario_management as scenario_funcs

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

def test_location_isolation(connection):
    """
    Verify that a location created by Tenant 1 is not visible to Tenant 2.
    """
    tenant_a = 1
    tenant_b = 2
    
    # 1. Create Location for Tenant A
    loc_id_a = create.add_location(
        tenant_id=tenant_a,
        name="Tenant A Hub",
        type="Hub",
        address_street="123 A St",
        city="City A",
        state="OR",
        zip_code="97000",
        phone="555-0001",
        latitude=45.0,
        longitude=-122.0,
        avg_load_minutes=30,
        avg_unload_minutes=30,
        conn=connection
    )
    connection.commit()
    
    # 2. Verify Tenant A can see it
    rows_a = read.view_locations(tenant_a, connection, ids=loc_id_a)
    assert len(rows_a) == 1
    assert rows_a[0]['name'] == "Tenant A Hub"
    
    # 3. Verify Tenant B CANNOT see it
    rows_b = read.view_locations(tenant_b, connection, ids=loc_id_a)
    assert len(rows_b) == 0
    
    # Cleanup
    delete.delete_location(tenant_a, loc_id_a, conn=connection)
    connection.commit()

def test_product_isolation(connection):
    """
    Verify that a product created by Tenant 1 is not visible to Tenant 2.
    """
    tenant_a = 1
    tenant_b = 2
    prod_code = "TENANT-TEST-PROD"
    
    # 1. Create for Tenant A
    create.add_product_master(tenant_a, prod_code, "Test Prod", "Dry", conn=connection)
    connection.commit()
    
    # 2. A sees it
    rows_a = read.view_products_master(tenant_a, connection, ids=prod_code)
    assert len(rows_a) == 1
    
    # 3. B does not
    rows_b = read.view_products_master(tenant_b, connection, ids=prod_code)
    assert len(rows_b) == 0
    
    # Cleanup
    delete.delete_product_master(tenant_a, prod_code, conn=connection)
    connection.commit()

def test_scenario_security(connection):
    """
    Verify that Tenant B cannot view or update Tenant A's scenario.
    """
    tenant_a = 1
    tenant_b = 2
    
    # 1. Setup minimal dependencies for Tenant A
    loc1 = create.add_location(tenant_a, "Loc1", "Hub", "A", "C", "S", "Z", "P", 0, 0, 10, 10, conn=connection)
    loc2 = create.add_location(tenant_a, "Loc2", "Store", "A", "C", "S", "Z", "P", 0, 0, 10, 10, conn=connection)
    route_a = create.add_route(tenant_a, "Route A", loc1, loc2, conn=connection)
    connection.commit()
    
    # 2. Create Scenario for Tenant A
    scen_a = scenario_funcs.create_scenario(
        tenant_id=tenant_a,
        route_id=route_a,
        total_revenue=100.00,
        conn=connection
    )
    
    # 3. Verify A sees scenario
    details_a = scenario_funcs.get_trip_details(tenant_a, scen_a, conn=connection)
    assert details_a is not None
    assert details_a['header']['scenario_id'] == scen_a
    
    # 4. Verify B does NOT see scenario (get_trip_details returns None)
    details_b = scenario_funcs.get_trip_details(tenant_b, scen_a, conn=connection)
    assert details_b is None
    
    # 5. Attempt Update by B on A's scenario (Should fail/return None)
    with pytest.raises(mysql_errors.DatabaseError) as excinfo:
        scenario_funcs.update_scenario(
            tenant_id=tenant_b,
            scenario_id=scen_a,
            total_revenue=9999.99,
            conn=connection
        )
    assert "scenario_id not found" in str(excinfo.value)
    
    # 6. Verify A's data is unchanged
    details_a_after = scenario_funcs.get_trip_details(tenant_a, scen_a, conn=connection)
    # Revenue should still be 100.00, not 9999.99
    assert details_a_after['header']['entered_revenue'] == Decimal('100.00')
    
    # Cleanup
    delete.delete_plan(tenant_a, scen_a, conn=connection)
    delete.delete_route(tenant_a, route_a, conn=connection)
    delete.delete_location(tenant_a, loc1, conn=connection)
    delete.delete_location(tenant_a, loc2, conn=connection)
    connection.commit()

def test_driver_isolation(connection):
    tenant_a = 1
    tenant_b = 2
    
    d_id = create.add_driver(tenant_a, "Driver A", 20.0, 15.0, conn=connection)
    connection.commit()
    
    rows_a = read.view_drivers(tenant_a, connection, ids=d_id)
    assert len(rows_a) == 1
    
    rows_b = read.view_drivers(tenant_b, connection, ids=d_id)
    assert len(rows_b) == 0
    
    delete.delete_driver(tenant_a, d_id, conn=connection)
    connection.commit()

def test_vehicle_isolation(connection):
    tenant_a = 1
    tenant_b = 2
    
    v_id = create.add_vehicle(tenant_a, "Truck A", 10.0, 0.5, 1000, 500, 10000, 1000, "Dry", conn=connection)
    connection.commit()
    
    rows_a = read.view_vehicles(tenant_a, connection, ids=v_id)
    assert len(rows_a) == 1
    
    rows_b = read.view_vehicles(tenant_b, connection, ids=v_id)
    assert len(rows_b) == 0
    
    delete.delete_vehicle(tenant_a, v_id, conn=connection)
    connection.commit()

def test_cross_tenant_deletion_attempt(connection):
    """
    Verify Tenant B cannot delete Tenant A's data.
    """
    tenant_a = 1
    tenant_b = 2
    
    loc_id = create.add_location(tenant_a, "Loc A", "Hub", "St", "C", "S", "Z", "P", 0, 0, 0, 0, conn=connection)
    connection.commit()
    
    # B tries to delete
    delete.delete_location(tenant_b, loc_id, conn=connection)
    connection.commit()
    
    # Verify it still exists for A
    rows = read.view_locations(tenant_a, connection, ids=loc_id)
    assert len(rows) == 1
    
    # Cleanup
    delete.delete_location(tenant_a, loc_id, conn=connection)
    connection.commit()

def test_cross_tenant_fk_violation(connection):
    """
    Verify Tenant A cannot create a route using Tenant B's location.
    """
    tenant_a = 1
    tenant_b = 2
    
    loc_b = create.add_location(tenant_b, "Loc B", "Hub", "St", "C", "S", "Z", "P", 0, 0, 0, 0, conn=connection)
    loc_a = create.add_location(tenant_a, "Loc A", "Hub", "St", "C", "S", "Z", "P", 0, 0, 0, 0, conn=connection)
    connection.commit()
    
    # A tries to create route from Loc A (valid) to Loc B (invalid for Tenant A)
    with pytest.raises(mysql_errors.IntegrityError):
        create.add_route(tenant_a, "Bad Route", loc_a, loc_b, conn=connection)
        
    # Cleanup
    delete.delete_location(tenant_b, loc_b, conn=connection)
    delete.delete_location(tenant_a, loc_a, conn=connection)
    connection.commit()

def test_supply_chain_isolation(connection):
    """
    Complex chain: Entity -> Supply -> Demand isolation
    """
    tenant_a = 1
    tenant_b = 2
    
    ent_a = create.add_entity(tenant_a, "Ent A", 0, conn=connection)
    loc_a = create.add_location(tenant_a, "Loc A", "Hub", "St", "C", "S", "Z", "P", 0, 0, 0, 0, conn=connection)
    prod_a = "PROD-A"
    create.add_product_master(tenant_a, prod_a, "P A", "Dry", conn=connection)
    connection.commit()
    
    # Create Supply for A
    sup_a = create.add_supply(tenant_a, ent_a, loc_a, prod_a, 100, 1, 1, 1, 10, conn=connection)
    connection.commit()
    
    # Verify B cannot see supply
    rows_b = read.view_supply(tenant_b, connection, ids=sup_a)
    assert len(rows_b) == 0
    
    # Verify B cannot create supply using A's entity (FK check)
    with pytest.raises(mysql_errors.IntegrityError):
        create.add_supply(tenant_b, ent_a, loc_a, prod_a, 100, 1, 1, 1, 10, conn=connection)
        
    # Cleanup
    delete.delete_supply(tenant_a, sup_a, conn=connection)
    delete.delete_entity(tenant_a, ent_a, conn=connection)
    delete.delete_location(tenant_a, loc_a, conn=connection)
    delete.delete_product_master(tenant_a, prod_a, conn=connection)
    connection.commit()