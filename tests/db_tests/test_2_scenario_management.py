import pytest
import os
import mysql.connector
import dotenv
from decimal import Decimal
import random
import string

# Update these imports to match where you saved the functions
import db.functions.simple_functions.read as read
import db.functions.simple_functions.delete as delete
import db.functions.scenario_management as scenario_funcs 

dotenv.load_dotenv()

# --- FIXTURES ---

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

@pytest.fixture(scope="function")
def dependencies(connection):
    """
    Fetches random existing dependencies from the DB.
    Only gets Route, Vehicle, and Driver.
    """
    # Get a Route
    routes = read.view_routes(connection)
    if not routes:
        pytest.fail("No Routes found in DB. Please seed data first.")
    route_id = random.choice(routes)['route_id']

    # Get a Vehicle
    vehicles = read.view_vehicles(connection)
    if not vehicles:
        pytest.fail("No Vehicles found in DB.")
    vehicle_id = random.choice(vehicles)['vehicle_id']

    # Get a Driver
    drivers = read.view_drivers(connection)
    if not drivers:
        pytest.fail("No Drivers found in DB.")
    driver_id = random.choice(drivers)['driver_id']
    
    return {
        "route_id": route_id,
        "vehicle_id": vehicle_id,
        "driver_id": driver_id
    }


def test_create_scenario(connection, dependencies):
    deps = dependencies
    
    # Value 1500.50 fits comfortably in DECIMAL(10,2)
    new_id = scenario_funcs.create_scenario(
        route_id=deps['route_id'],
        total_revenue=1500.50, 
        vehicle_id=deps['vehicle_id'],
        driver_id=deps['driver_id'],
        run_date="2026-06-01",
        current_gas_price=4.50,
        conn=connection
    )
    
    assert new_id is not None
    
    # Verify via get_trip_details
    details = scenario_funcs.get_trip_details(new_id, conn=connection)
    assert details is not None
    assert details['header']['scenario_id'] == new_id

    # Cleanup
    delete.delete_plan(new_id, conn=connection)


def test_update_scenario(connection, dependencies):
    deps = dependencies
    
    # Create
    scenario_id = scenario_funcs.create_scenario(
        route_id=deps['route_id'],
        total_revenue=1000.00,
        vehicle_id=deps['vehicle_id'],
        driver_id=deps['driver_id'],
        conn=connection 
    )
    
    # Update
    scenario_funcs.update_scenario(
        scenario_id,
        total_revenue=2500.00,
        current_gas_price=5.25,
        conn=connection
    )
    
    # Verify
    details = scenario_funcs.get_trip_details(scenario_id, conn=connection)
    header = details['header']
    
    assert header['gas_price'] == Decimal('5.25') 
    
    # Cleanup
    delete.delete_plan(scenario_id, conn=connection)


def test_add_manifest_items(connection, dependencies):
    deps = dependencies
    
    # Create Scenario
    scenario_id = scenario_funcs.create_scenario(
        route_id=deps['route_id'],
        total_revenue=5000.00,
        vehicle_id=deps['vehicle_id'],
        driver_id=deps['driver_id'],
        conn=connection
    )
    
    # Add Item (No Supply/Demand IDs)
    random_name = ''.join(random.choices(string.ascii_uppercase, k=5))
    
    scenario_funcs.add_manifest_items(
        scenario_id=scenario_id,
        quantity_loaded=100, 
        supply_id=None,
        demand_id=None,
        item_name=f"Item_{random_name}",
        cost_per_item=5.00,
        price_per_item=12.50,
        items_per_unit=10,
        unit_weight=50,
        conn=connection
    )
    
    # Verify
    details = scenario_funcs.get_trip_details(scenario_id, conn=connection)
    items = details['items']
    
    assert len(items) == 1
    item = items[0]
    
    assert item['product_name'] == f"Item_{random_name}"
    assert item['quantity_loaded'] == 100
    assert item['price_per_item'] == Decimal('12.50')
    
    # Cleanup
    delete.delete_plan(scenario_id, conn=connection)


def test_delete_scenario(connection, dependencies):
    deps = dependencies
    
    # Create
    scenario_id = scenario_funcs.create_scenario(
        route_id=deps['route_id'],
        total_revenue=2000.00,
        vehicle_id=deps['vehicle_id'],
        driver_id=deps['driver_id'],
        conn=connection 
    )

    # Add Item
    manifest_id = scenario_funcs.add_manifest_items(scenario_id, "DeleteMe", 1, conn=connection)
    connection.commit()

    manifest_detail = read.view_manifest_items(ids=[manifest_id], conn=connection)
    assert manifest_detail[0]['item_name'] == "DeleteMe"

    # Delete
    delete.delete_plan(scenario_id, conn=connection)

    # Verify Gone
    details = scenario_funcs.get_trip_details(scenario_id, conn=connection)

    manifest_id_returned = read.view_manifest_items(ids=[manifest_id], conn=connection)
    assert manifest_id_returned == []
    assert details is None