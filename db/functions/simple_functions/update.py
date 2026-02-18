from ..connect import get_db
from decimal import Decimal

LOCATION_TYPES = {"Hub", "Store", "Farm"}
STORAGE_TYPES = {"Dry", "Ref", "Frz"}
VEHICLE_STORAGE_TYPES = {"Dry", "Ref", "Frz", "Multi"}


def _execute_update_proc(proc_name, args, conn=None):
    should_close = False
    if conn is None:
        conn = get_db()
        should_close = True
    
    if conn is None:
        raise RuntimeError("Failed to connect to database")

    try:
        cur = conn.cursor()
        cur.callproc(proc_name, args)
        conn.commit()
        cur.close()
    finally:
        if should_close and conn:
            conn.close()


def _to_int(x):
    return int(x) if x not in (None, "") else None


def _to_dec(x):
    return Decimal(str(x)) if x not in (None, "") else Decimal("0")


def update_location(
    tenant_id, location_id, name, type, address_street, city, state, zip_code, phone,
    latitude, longitude, avg_load_minutes, avg_unload_minutes,
    conn=None
):
    if type not in LOCATION_TYPES:
        raise ValueError(f"Invalid location type: {type}")

    args = [
        tenant_id, location_id, name, type, address_street, city, state, zip_code, phone,
        latitude, longitude, avg_load_minutes, avg_unload_minutes
    ]
    _execute_update_proc("update_location", args, conn)


def update_product_master(tenant_id, product_code, name, storage_type, conn=None):
    if storage_type not in STORAGE_TYPES:
        raise ValueError(f"Invalid storage type: {storage_type}")

    args = [tenant_id, product_code, name, storage_type]
    _execute_update_proc("update_product_master", args, conn)


def update_driver(tenant_id, driver_id, name, hourly_drive_wage, hourly_load_wage, conn=None):
    args = [tenant_id, driver_id, name, hourly_drive_wage, hourly_load_wage]
    _execute_update_proc("update_driver", args, conn)


def update_vehicle(
    tenant_id, vehicle_id, name, mpg, depreciation_per_mile, annual_insurance_cost,
    annual_maintenance_cost, max_weight_lbs, max_volume_cubic_ft, storage_type,
    conn=None
):
    if storage_type not in VEHICLE_STORAGE_TYPES:
        raise ValueError(f"Invalid vehicle storage type: {storage_type}")

    args = [
        tenant_id, vehicle_id, name, mpg, depreciation_per_mile, annual_insurance_cost,
        annual_maintenance_cost, max_weight_lbs, max_volume_cubic_ft, storage_type
    ]
    _execute_update_proc("update_vehicle", args, conn)


def update_entity(tenant_id, entity_id, name, entity_min_profit, conn=None):
    args = [tenant_id, entity_id, name, entity_min_profit]
    _execute_update_proc("update_entity", args, conn)


def update_supply(
    tenant_id, supply_id, entity_id, location_id, product_code, quantity_available,
    unit_weight_lbs, unit_volume_cu_ft, items_per_handling_unit, cost_per_item,
    conn=None
):
    args = [
        tenant_id, supply_id, entity_id, location_id, product_code, quantity_available,
        unit_weight_lbs, unit_volume_cu_ft, items_per_handling_unit, cost_per_item
    ]
    _execute_update_proc("update_supply", args, conn)


def update_demand(tenant_id, demand_id, location_id, product_code, quantity_needed, max_price, conn=None):
    args = [tenant_id, demand_id, location_id, product_code, quantity_needed, max_price]
    _execute_update_proc("update_demand", args, conn)


def update_route(tenant_id, route_id, name, origin_location_id, dest_location_id, conn=None):
    args = [tenant_id, route_id, name, origin_location_id, dest_location_id]
    _execute_update_proc("update_route", args, conn)


def update_scenario(
    tenant_id, scenario_id, route_id, vehicle_id, driver_id, run_date,
    snapshot_driver_wage, snapshot_driver_load_wage,
    snapshot_vehicle_mpg, snapshot_gas_price,
    snapshot_daily_insurance, snapshot_daily_maintenance_cost,
    snapshot_planned_load_minutes, snapshot_planned_unload_minutes,
    actual_load_minutes, actual_unload_minutes, snapshot_total_revenue,
    conn=None
):
    args = [
        tenant_id, scenario_id, route_id, vehicle_id, driver_id, run_date,
        snapshot_driver_wage, snapshot_driver_load_wage,
        snapshot_vehicle_mpg, snapshot_gas_price,
        snapshot_daily_insurance, snapshot_daily_maintenance_cost,
        snapshot_planned_load_minutes, snapshot_planned_unload_minutes,
        actual_load_minutes, actual_unload_minutes, snapshot_total_revenue
    ]
    _execute_update_proc("update_scenario", args, conn)


def update_manifest_item(
    tenant_id,
    manifest_item_id,
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

    args = [
        tenant_id,
        int(manifest_item_id),
        int(scenario_id),
        _to_int(supply_id),
        _to_int(demand_id),
        str(item_name),
        _to_dec(quantity_loaded),
        _to_dec(snapshot_cost_per_item),
        _to_int(snapshot_items_per_unit) or 1,
        _to_dec(snapshot_unit_weight),
        _to_dec(snapshot_unit_volume),
        _to_dec(snapshot_price_per_item),
    ]
    _execute_update_proc("update_manifest_item", args, conn)