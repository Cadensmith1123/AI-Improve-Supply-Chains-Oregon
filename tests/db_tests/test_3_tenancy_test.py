import pytest
import os
import mysql.connector
import dotenv
from datetime import date
from decimal import Decimal
from mysql.connector import errors as mysql_errors

import db.functions.simple_functions.read as read
import db.functions.simple_functions.create as create
import db.functions.simple_functions.update as update
import db.functions.simple_functions.delete as delete

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

def _to_int(x):
    return int(x) if x not in (None, "") else None


def _create_scenario(connection, tenant_id, route_id, total_revenue,
                     vehicle_id=None, driver_id=None):
    """
    Create a scenario for an EXPLICIT tenant via the create_trip_header proc.

    scenario_management.create_scenario() resolves the tenant from flask.g,
    which is not available in these DB-layer tests, so we drive the underlying
    proc directly with an explicit tenant_id (mirroring its argument list).
    Returns the new scenario_id.
    """
    cur = connection.cursor()
    args = [
        tenant_id, int(route_id),
        _to_int(vehicle_id), _to_int(driver_id), date.today(),
        Decimal("0.0"), Decimal(str(total_revenue)),
        Decimal("0.0"), Decimal("0.0"), Decimal("0.0"),
        0,  # OUT p_new_scenario_id placeholder
    ]
    result = cur.callproc("create_trip_header", args)
    connection.commit()
    cur.close()
    return result[-1]

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

def test_scenario_isolation(connection):
    """
    Verify Tenant B can neither read nor delete Tenant A's scenario.
    """
    tenant_a = 1
    tenant_b = 2

    # 1. Setup minimal dependencies + scenario for Tenant A
    loc1 = create.add_location(tenant_a, "Loc1", "Hub", "A", "C", "OR", "97000", "P", 0, 0, 10, 10, conn=connection)
    loc2 = create.add_location(tenant_a, "Loc2", "Store", "A", "C", "OR", "97000", "P", 0, 0, 10, 10, conn=connection)
    route_a = create.add_route(tenant_a, "Route A", loc1, loc2, conn=connection)
    connection.commit()

    scen_a = _create_scenario(connection, tenant_a, route_a, 100.00)

    # 2. Tenant A sees its scenario
    rows_a = read.view_scenarios(tenant_a, connection, ids=scen_a)
    assert len(rows_a) == 1
    assert rows_a[0]['scenario_id'] == scen_a

    # 3. Tenant B does NOT see it
    rows_b = read.view_scenarios(tenant_b, connection, ids=scen_a)
    assert len(rows_b) == 0

    # 4. Tenant B cannot delete A's scenario (scoped delete affects 0 rows)
    delete.delete_plan(tenant_b, scen_a, conn=connection)
    connection.commit()
    assert len(read.view_scenarios(tenant_a, connection, ids=scen_a)) == 1

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
    
    v_id = create.add_vehicle(tenant_a, "Truck A", 10.0, 45000.00, 20000.00, 5000.00, 1000, 500, 10000, 1000, "Dry", conn=connection)
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


def test_route_isolation(connection):
    """
    Test plan integration priority: create a route under Tenant A, query it
    with Tenant B credentials -> assert empty result.
    """
    tenant_a = 1
    tenant_b = 2

    loc1 = create.add_location(tenant_a, "RouteIso Origin", "Hub", "St", "C", "OR", "97000", "P", 0, 0, 10, 10, conn=connection)
    loc2 = create.add_location(tenant_a, "RouteIso Dest", "Store", "St", "C", "OR", "97000", "P", 0, 0, 10, 10, conn=connection)
    route_a = create.add_route(tenant_a, "RouteIso A", loc1, loc2, conn=connection)
    connection.commit()

    # A sees its route
    rows_a = read.view_routes(tenant_a, connection, ids=route_a)
    assert len(rows_a) == 1
    assert rows_a[0]['name'] == "RouteIso A"

    # B sees nothing
    rows_b = read.view_routes(tenant_b, connection, ids=route_a)
    assert len(rows_b) == 0

    # Cleanup
    delete.delete_route(tenant_a, route_a, conn=connection)
    delete.delete_location(tenant_a, loc1, conn=connection)
    delete.delete_location(tenant_a, loc2, conn=connection)
    connection.commit()


def test_cross_tenant_update_is_silent_noop(connection):
    """
    Test plan (Multi-Tenant Data Isolation): writes must never cross tenant
    boundaries. Each update proc filters WHERE id = ? AND tenant_id = ?, so a
    write attempted by Tenant B against Tenant A's records affects zero rows
    and raises no error. Verify A's data is left intact.
    """
    tenant_a = 1
    tenant_b = 2

    loc_a = create.add_location(tenant_a, "Orig Loc", "Hub", "St", "C", "OR", "97000", "555", 0, 0, 10, 10, conn=connection)
    loc_a2 = create.add_location(tenant_a, "Orig Dest", "Store", "St", "C", "OR", "97000", "555", 0, 0, 10, 10, conn=connection)
    drv_a = create.add_driver(tenant_a, "Orig Driver", 20.0, 15.0, conn=connection)
    veh_a = create.add_vehicle(tenant_a, "Orig Truck", 10.0, 45000.00, 20000.00, 5000.00, 1000, 500, 10000, 1000, "Dry", conn=connection)
    route_a = create.add_route(tenant_a, "Orig Route", loc_a, loc_a2, conn=connection)
    connection.commit()

    # Tenant B attempts to overwrite each of A's records (no exception expected).
    update.update_location(tenant_b, loc_a, "HACKED", "Hub", "X", "X", "OR", "00000", "000", 1, 1, 99, 99, conn=connection)
    update.update_driver(tenant_b, drv_a, "HACKED", 1.0, 1.0, conn=connection)
    update.update_vehicle(tenant_b, veh_a, "HACKED", 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1, 1, "Dry", conn=connection)
    update.update_route(tenant_b, route_a, "HACKED", loc_a, loc_a2, conn=connection)
    connection.commit()

    # A's data is unchanged.
    assert read.view_locations(tenant_a, connection, ids=loc_a)[0]['name'] == "Orig Loc"
    assert read.view_drivers(tenant_a, connection, ids=drv_a)[0]['name'] == "Orig Driver"
    assert read.view_vehicles(tenant_a, connection, ids=veh_a)[0]['name'] == "Orig Truck"
    assert read.view_routes(tenant_a, connection, ids=route_a)[0]['name'] == "Orig Route"

    # Cleanup
    delete.delete_route(tenant_a, route_a, conn=connection)
    delete.delete_driver(tenant_a, drv_a, conn=connection)
    delete.delete_vehicle(tenant_a, veh_a, conn=connection)
    delete.delete_location(tenant_a, loc_a, conn=connection)
    delete.delete_location(tenant_a, loc_a2, conn=connection)
    connection.commit()


def test_listing_does_not_leak_across_tenants(connection):
    """
    An unscoped 'view all' (no ids filter) must return only the caller's
    tenant rows. Seed one location for A and one for B, then assert neither
    tenant's full listing contains the other's id.
    """
    tenant_a = 1
    tenant_b = 2

    loc_a = create.add_location(tenant_a, "Leak Test A", "Hub", "St", "C", "OR", "97000", "555", 0, 0, 10, 10, conn=connection)
    loc_b = create.add_location(tenant_b, "Leak Test B", "Hub", "St", "C", "OR", "97000", "555", 0, 0, 10, 10, conn=connection)
    connection.commit()

    a_ids = {r['location_id'] for r in read.view_locations(tenant_a, connection)}
    b_ids = {r['location_id'] for r in read.view_locations(tenant_b, connection)}

    assert loc_a in a_ids
    assert loc_a not in b_ids
    assert loc_b in b_ids
    assert loc_b not in a_ids

    # Cleanup
    delete.delete_location(tenant_a, loc_a, conn=connection)
    delete.delete_location(tenant_b, loc_b, conn=connection)
    connection.commit()


def test_manifest_item_isolation(connection):
    """
    Manifest items belonging to Tenant A's scenario must not be visible to
    Tenant B, even when B requests the exact manifest_item_id.
    """
    tenant_a = 1
    tenant_b = 2

    loc1 = create.add_location(tenant_a, "Manifest Origin", "Hub", "St", "C", "OR", "97000", "P", 0, 0, 10, 10, conn=connection)
    loc2 = create.add_location(tenant_a, "Manifest Dest", "Store", "St", "C", "OR", "97000", "P", 0, 0, 10, 10, conn=connection)
    route_a = create.add_route(tenant_a, "Manifest Route", loc1, loc2, conn=connection)
    connection.commit()

    scen_a = _create_scenario(connection, tenant_a, route_a, 500.00)
    mi_id = create.add_manifest_item(tenant_a, scen_a, "Secret Cargo", 10, conn=connection)
    connection.commit()

    # A sees the item
    rows_a = read.view_manifest_items(tenant_a, ids=[mi_id], conn=connection)
    assert len(rows_a) == 1
    assert rows_a[0]['item_name'] == "Secret Cargo"

    # B sees nothing
    rows_b = read.view_manifest_items(tenant_b, ids=[mi_id], conn=connection)
    assert len(rows_b) == 0

    # Cleanup (delete_plan cascades to manifest items)
    delete.delete_plan(tenant_a, scen_a, conn=connection)
    delete.delete_route(tenant_a, route_a, conn=connection)
    delete.delete_location(tenant_a, loc1, conn=connection)
    delete.delete_location(tenant_a, loc2, conn=connection)
    connection.commit()