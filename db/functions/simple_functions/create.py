from ..connect import get_db
from decimal import Decimal

LOCATION_TYPES = {"Hub", "Store", "Farm"}
STORAGE_TYPES = {"Dry", "Ref", "Frz"}
VEHICLE_STORAGE_TYPES = {"Dry", "Ref", "Frz", "Multi"}


def add_location(
    name, type, address_street, city, state, zip_code, phone,
    latitude, longitude, avg_load_minutes, avg_unload_minutes,
    conn=None
):
    if type not in LOCATION_TYPES:
        raise ValueError(f"Invalid location type: {type}")

    if conn is None:
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


def add_product_master(product_code, name, storage_type, conn=None):
    if storage_type not in STORAGE_TYPES:
        raise ValueError(f"Invalid storage type: {storage_type}")

    if conn is None:
        conn = get_db()

    cur = conn.cursor()
    cur.callproc("add_product_master", [product_code, name, storage_type])
    for r in cur.stored_results():
        new_id = r.fetchone()[0]
    conn.commit()
    cur.close()
    return new_id


def add_driver(name, hourly_drive_wage, hourly_load_wage, conn=None):
    if conn is None:
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
    max_weight_lbs, max_volume_cubic_ft, storage_type,
    conn=None
    ):
    if storage_type not in VEHICLE_STORAGE_TYPES:
        raise ValueError(f"Invalid vehicle storage type: {storage_type}")

    if conn is None:
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


def add_entity(name, entity_min_profit, conn=None):
    if conn is None:
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
    unit_weight_lbs, unit_volume_cu_ft, items_per_handling_unit, cost_per_item,
    conn=None
):
    if conn is None:
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


def add_demand(location_id, product_code, quantity_needed, max_price, conn=None):
    if conn is None:
        conn = get_db()

    cur = conn.cursor()
    cur.callproc("add_demand", [location_id, product_code, quantity_needed, max_price])
    for r in cur.stored_results():
        new_id = r.fetchone()[0]
    conn.commit()
    cur.close()
    return new_id


def add_route(name, origin_location_id, dest_location_id, conn=None):
    if conn is None:
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
    snapshot_vehicle_mpg, snapshot_gas_price,
    snapshot_daily_insurance, snapshot_daily_maintenance_cost,
    snapshot_planned_load_minutes, snapshot_planned_unload_minutes,
    actual_load_minutes, actual_unload_minutes, snapshot_total_revenue,
    conn=None
):
    if conn is None:
        conn = get_db()

    cur = conn.cursor()
    cur.callproc("add_scenario", [
        route_id, vehicle_id, driver_id, run_date,
        snapshot_driver_wage, snapshot_driver_load_wage,
        snapshot_vehicle_mpg, snapshot_gas_price,
        snapshot_daily_insurance, snapshot_daily_maintenance_cost,
        snapshot_planned_load_minutes, snapshot_planned_unload_minutes,
        actual_load_minutes, actual_unload_minutes, snapshot_total_revenue
    ])
    for r in cur.stored_results():
        new_id = r.fetchone()[0]
    conn.commit()
    cur.close()
    return new_id


def add_manifest_item(
    scenario_id,
    item_name,
    quantity_loaded,
    supply_id=None,
    demand_id=None,
    snapshot_cost_per_item=0.0,
    snapshot_items_per_unit=1,
    snapshot_unit_weight=0.0,
    snapshot_unit_volume=0.0,   
    snapshot_price_per_item=0.0,
    conn=None
):
    if scenario_id in (None, ""):
        raise ValueError("scenario_id is required")
    if item_name in (None, ""):
        raise ValueError("item_name is required")
    if quantity_loaded in (None, ""):
        raise ValueError("quantity_loaded is required")

    def _to_int(x):
        return int(x) if x not in (None, "") else None

    def _to_dec(x):
        return Decimal(str(x)) if x not in (None, "") else Decimal("0")

    if conn is None:
        conn = get_db()

    args = [
        int(scenario_id),              # p_scenario_id
        _to_int(supply_id),            # p_supply_id
        _to_int(demand_id),            # p_demand_id
        str(item_name),                # p_item_name
        _to_dec(quantity_loaded),      # p_quantity_loaded
        _to_dec(snapshot_cost_per_item),
        _to_int(snapshot_items_per_unit) or 1,
        _to_dec(snapshot_unit_weight),
        _to_dec(snapshot_unit_volume),
        _to_dec(snapshot_price_per_item),
    ]

    cur = conn.cursor()
    cur.callproc("add_manifest_item", args)

    new_id = None
    for r in cur.stored_results():
        row = r.fetchone()
        if row:
            new_id = row[0]

    conn.commit()
    cur.close()

    if new_id is None:
        raise RuntimeError("add_manifest_item did not return new_id")

    return new_id