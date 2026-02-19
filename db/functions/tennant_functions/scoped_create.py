from flask import g
from ..simple_functions.create import (
    add_location,
    add_product_master,
    add_driver,
    add_vehicle,
    add_entity,
    add_supply,
    add_demand,
    add_route,
    add_scenario,
    add_manifest_item,
)


def _tenant_id():
    """
    Fetch tenant_id from request context.
    Fail loudly if missing.
    """
    tid = getattr(g, "tenant_id", None)
    if tid is None:
        raise RuntimeError("Missing g.tenant_id (auth middleware not run?)")
    return int(tid)


def add_location_scoped(*, name, type, address_street=None, city=None, state=None,
                        zip_code=None, phone=None, latitude=None, longitude=None,
                        avg_load_minutes=None, avg_unload_minutes=None, conn=None):
    return add_location(
        _tenant_id(),
        name, type, address_street, city, state, zip_code, phone,
        latitude, longitude, avg_load_minutes, avg_unload_minutes,
        conn=conn
    )

def add_product_master_scoped(*, product_code, name, storage_type, conn=None):
    return add_product_master(_tenant_id(), product_code, name, storage_type, conn=conn)

def add_driver_scoped(*, name, hourly_drive_wage, hourly_load_wage, conn=None):
    return add_driver(_tenant_id(), name, hourly_drive_wage, hourly_load_wage, conn=conn)

def add_vehicle_scoped(*, name, mpg, depreciation_per_mile=0.0, annual_insurance_cost=0.0,
                       annual_maintenance_cost=0.0, max_weight_lbs=None, max_volume_cubic_ft=None,
                       storage_type=None, conn=None):
    return add_vehicle(
        _tenant_id(),
        name, mpg, depreciation_per_mile, annual_insurance_cost, annual_maintenance_cost,
        max_weight_lbs, max_volume_cubic_ft, storage_type,
        conn=conn
    )

def add_entity_scoped(*, name, entity_min_profit=0.0, conn=None):
    return add_entity(_tenant_id(), name, entity_min_profit, conn=conn)

def add_supply_scoped(*, entity_id, location_id, product_code, quantity_available,
                      unit_weight_lbs=0.0, unit_volume_cu_ft=0.0, items_per_handling_unit=1,
                      cost_per_item=0.0, conn=None):
    return add_supply(
        _tenant_id(),
        entity_id, location_id, product_code, quantity_available,
        unit_weight_lbs, unit_volume_cu_ft, items_per_handling_unit, cost_per_item,
        conn=conn
    )

def add_demand_scoped(*, location_id, product_code, quantity_needed, max_price=0.0, conn=None):
    return add_demand(_tenant_id(), location_id, product_code, quantity_needed, max_price, conn=conn)

def add_route_scoped(*, name=None, origin_location_id=None, dest_location_id=None, conn=None):
    return add_route(_tenant_id(), name, origin_location_id, dest_location_id, conn=conn)

def add_scenario_scoped(*, route_id, vehicle_id=None, driver_id=None, run_date=None,
                        snapshot_driver_wage=None, snapshot_driver_load_wage=None,
                        snapshot_vehicle_mpg=None, snapshot_gas_price=None,
                        snapshot_daily_insurance=None, snapshot_daily_maintenance_cost=None,
                        snapshot_planned_load_minutes=None, snapshot_planned_unload_minutes=None,
                        actual_load_minutes=0, actual_unload_minutes=0, snapshot_total_revenue=0.0,
                        conn=None):
    return add_scenario(
        _tenant_id(),
        route_id, vehicle_id, driver_id, run_date,
        snapshot_driver_wage, snapshot_driver_load_wage,
        snapshot_vehicle_mpg, snapshot_gas_price,
        snapshot_daily_insurance, snapshot_daily_maintenance_cost,
        snapshot_planned_load_minutes, snapshot_planned_unload_minutes,
        actual_load_minutes, actual_unload_minutes, snapshot_total_revenue,
        conn=conn
    )

def add_manifest_item_scoped(*, scenario_id, item_name, quantity_loaded,
                             supply_id=None, demand_id=None,
                             snapshot_cost_per_item=0.0, snapshot_items_per_unit=1,
                             snapshot_unit_weight=0.0, snapshot_unit_volume=0.0,
                             snapshot_price_per_item=0.0, conn=None):
    return add_manifest_item(
        _tenant_id(),
        scenario_id, item_name, quantity_loaded,
        supply_id=supply_id, demand_id=demand_id,
        snapshot_cost_per_item=snapshot_cost_per_item,
        snapshot_items_per_unit=snapshot_items_per_unit,
        snapshot_unit_weight=snapshot_unit_weight,
        snapshot_unit_volume=snapshot_unit_volume,
        snapshot_price_per_item=snapshot_price_per_item,
        conn=conn
    )