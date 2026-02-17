from ..connect import get_db, execute_creation_proc
from decimal import Decimal

LOCATION_TYPES = {"Hub", "Store", "Farm"}
STORAGE_TYPES = {"Dry", "Ref", "Frz"}
VEHICLE_STORAGE_TYPES = {"Dry", "Ref", "Frz", "Multi"}


def add_location(
    tenant_id,
    name, type, address_street, city, state, zip_code, phone,
    latitude, longitude, avg_load_minutes, avg_unload_minutes,
    conn=None
):
    if type not in LOCATION_TYPES:
        raise ValueError(f"Invalid location type: {type}")

    args = [
        tenant_id,
        name, type, address_street, city, state, zip_code, phone,
        latitude, longitude, avg_load_minutes, avg_unload_minutes
    ]
    return execute_creation_proc("add_location", args, conn)


def add_product_master(tenant_id, product_code, name, storage_type, conn=None):
    if storage_type not in STORAGE_TYPES:
        raise ValueError(f"Invalid storage type: {storage_type}")

    args = [tenant_id, product_code, name, storage_type]
    return execute_creation_proc("add_product_master", args, conn)


def add_driver(tenant_id, name, hourly_drive_wage, hourly_load_wage, conn=None):
    args = [tenant_id, name, hourly_drive_wage, hourly_load_wage]
    return execute_creation_proc("add_driver", args, conn)


def add_vehicle(
    tenant_id,
    name, mpg, depreciation_per_mile, annual_insurance_cost, annual_maintenance_cost,
    max_weight_lbs, max_volume_cubic_ft, storage_type,
    conn=None
    ):
    if storage_type not in VEHICLE_STORAGE_TYPES:
        raise ValueError(f"Invalid vehicle storage type: {storage_type}")

    args = [
        tenant_id,
        name, mpg, depreciation_per_mile, annual_insurance_cost,
        annual_maintenance_cost, max_weight_lbs, max_volume_cubic_ft, storage_type
    ]
    return execute_creation_proc("add_vehicle", args, conn)


def add_entity(tenant_id, name, entity_min_profit, conn=None):
    args = [tenant_id, name, entity_min_profit]
    return execute_creation_proc("add_entity", args, conn)


def add_supply(
    tenant_id,
    entity_id, location_id, product_code, quantity_available,
    unit_weight_lbs, unit_volume_cu_ft, items_per_handling_unit, cost_per_item,
    conn=None
):
    args = [
        tenant_id,
        entity_id, location_id, product_code, quantity_available,
        unit_weight_lbs, unit_volume_cu_ft, items_per_handling_unit, cost_per_item
    ]
    return execute_creation_proc("add_supply", args, conn)


def add_demand(tenant_id, location_id, product_code, quantity_needed, max_price, conn=None):
    args = [tenant_id, location_id, product_code, quantity_needed, max_price]
    return execute_creation_proc("add_demand", args, conn)


def add_route(tenant_id, name, origin_location_id, dest_location_id, conn=None):
    args = [tenant_id, name, origin_location_id, dest_location_id]
    return execute_creation_proc("add_route", args, conn)


def add_scenario(
    tenant_id,
    route_id, vehicle_id, driver_id, run_date,
    snapshot_driver_wage, snapshot_driver_load_wage,
    snapshot_vehicle_mpg, snapshot_gas_price,
    snapshot_daily_insurance, snapshot_daily_maintenance_cost,
    snapshot_planned_load_minutes, snapshot_planned_unload_minutes,
    actual_load_minutes, actual_unload_minutes, snapshot_total_revenue,
    conn=None
):
    args = [
        tenant_id,
        route_id, vehicle_id, driver_id, run_date,
        snapshot_driver_wage, snapshot_driver_load_wage,
        snapshot_vehicle_mpg, snapshot_gas_price,
        snapshot_daily_insurance, snapshot_daily_maintenance_cost,
        snapshot_planned_load_minutes, snapshot_planned_unload_minutes,
        actual_load_minutes, actual_unload_minutes, snapshot_total_revenue
    ]
    return execute_creation_proc("add_scenario", args, conn)


def add_manifest_item(
    tenant_id,
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

    args = [
        tenant_id,
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

    new_id = execute_creation_proc("add_manifest_item", args, conn)

    if new_id is None:
        raise RuntimeError("add_manifest_item did not return new_id")

    return new_id