from ..connect import get_db

LOCATION_TYPES = {"Hub", "Store", "Farm"}
STORAGE_TYPES = {"Dry", "Ref", "Frz"}
VEHICLE_STORAGE_TYPES = {"Dry", "Ref", "Frz", "Multi"}


def add_location(
    name, type, address_street, city, state, zip_code, phone,
    latitude, longitude, avg_load_minutes, avg_unload_minutes
):
    if type not in LOCATION_TYPES:
        raise ValueError(f"Invalid location type: {type}")

    conn = get_db()
    cur = conn.cursor()
    cur.callproc("add_location", [
        name, type, address_street, city, state, zip_code, phone,
        latitude, longitude, avg_load_minutes, avg_unload_minutes
    ])
    for r in cur.stored_results():
        new_id = r.fetchone()[0]
    conn.commit()
    cur.close()
    return new_id


def add_product_master(product_code, name, storage_type):
    if storage_type not in STORAGE_TYPES:
        raise ValueError(f"Invalid storage type: {storage_type}")

    conn = get_db()
    cur = conn.cursor()
    cur.callproc("add_product_master", [product_code, name, storage_type])
    for r in cur.stored_results():
        new_id = r.fetchone()[0]
    conn.commit()
    cur.close()
    return new_id


def add_driver(name, hourly_drive_wage, hourly_load_wage):
    conn = get_db()
    cur = conn.cursor()
    cur.callproc("add_driver", [name, hourly_drive_wage, hourly_load_wage])
    for r in cur.stored_results():
        new_id = r.fetchone()[0]
    conn.commit()
    cur.close()
    return new_id


def add_vehicle(
    name, mpg, depreciation_per_mile, annual_insurance_cost,
    max_weight_lbs, max_volume_cubic_ft, storage_type
    ):
    if storage_type not in VEHICLE_STORAGE_TYPES:
        raise ValueError(f"Invalid vehicle storage type: {storage_type}")

    conn = get_db()
    cur = conn.cursor()
    cur.callproc("add_vehicle", [
        name, mpg, depreciation_per_mile, annual_insurance_cost,
        max_weight_lbs, max_volume_cubic_ft, storage_type
    ])
    for r in cur.stored_results():
        new_id = r.fetchone()[0]
    conn.commit()
    cur.close()
    return new_id


def add_entity(name, entity_min_profit):
    conn = get_db()
    cur = conn.cursor()
    cur.callproc("add_entity", [name, entity_min_profit])
    for r in cur.stored_results():
        new_id = r.fetchone()[0]
    conn.commit()
    cur.close()
    return new_id


def add_supply(
    entity_id, location_id, product_code, quantity_available,
    unit_weight_lbs, unit_volume_cu_ft, items_per_handling_unit, cost_per_item
):
    conn = get_db()
    cur = conn.cursor()
    cur.callproc("add_supply", [
        entity_id, location_id, product_code, quantity_available,
        unit_weight_lbs, unit_volume_cu_ft, items_per_handling_unit, cost_per_item
    ])
    for r in cur.stored_results():
        new_id = r.fetchone()[0]
    conn.commit()
    cur.close()
    return new_id


def add_demand(location_id, product_code, quantity_needed, max_price):
    conn = get_db()
    cur = conn.cursor()
    cur.callproc("add_demand", [location_id, product_code, quantity_needed, max_price])
    for r in cur.stored_results():
        new_id = r.fetchone()[0]
    conn.commit()
    cur.close()
    return new_id


def add_route(name, origin_location_id, dest_location_id):
    conn = get_db()
    cur = conn.cursor()
    cur.callproc("add_route", [name, origin_location_id, dest_location_id])
    for r in cur.stored_results():
        new_id = r.fetchone()[0]
    conn.commit()
    cur.close()
    return new_id


def add_scenario(
    route_id, vehicle_id, driver_id, run_date,
    snapshot_driver_wage, snapshot_driver_load_wage,
    snapshot_vehicle_mpg, snapshot_gas_price, snapshot_daily_insurance,
    snapshot_planned_load_minutes, snapshot_planned_unload_minutes,
    actual_load_minutes, actual_unload_minutes, snapshot_total_revenue
):
    conn = get_db()
    cur = conn.cursor()
    cur.callproc("add_scenario", [
        route_id, vehicle_id, driver_id, run_date,
        snapshot_driver_wage, snapshot_driver_load_wage,
        snapshot_vehicle_mpg, snapshot_gas_price, snapshot_daily_insurance,
        snapshot_planned_load_minutes, snapshot_planned_unload_minutes,
        actual_load_minutes, actual_unload_minutes, snapshot_total_revenue
    ])
    for r in cur.stored_results():
        new_id = r.fetchone()[0]
    conn.commit()
    cur.close()
    return new_id


def add_manifest_item(
    scenario_id, supply_id, demand_id, quantity_loaded,
    snapshot_cost_per_item, snapshot_items_per_unit,
    snapshot_unit_weight, snapshot_price_per_item
):
    conn = get_db()
    cur = conn.cursor()
    cur.callproc("add_manifest_item", [
        scenario_id, supply_id, demand_id, quantity_loaded,
        snapshot_cost_per_item, snapshot_items_per_unit,
        snapshot_unit_weight, snapshot_price_per_item
    ])
    for r in cur.stored_results():
        new_id = r.fetchone()[0]
    conn.commit()
    cur.close()
    return new_id
