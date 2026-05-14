from flask import g
from ..simple_functions.update import (
    update_location,
    update_product_master,
    update_driver,
    update_vehicle,
    update_entity,
    update_supply,
    update_demand,
    update_route,
    update_scenario,
    update_manifest_item,
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


def update_location_scoped(*, location_id, name, type, address_street, city, state, zip_code, phone,
                           latitude, longitude, avg_load_minutes, avg_unload_minutes, conn=None):
    return update_location(
        _tenant_id(),
        location_id, name, type, address_street, city, state, zip_code, phone,
        latitude, longitude, avg_load_minutes, avg_unload_minutes,
        conn=conn
    )


def update_product_master_scoped(*, product_code, name, storage_type, conn=None):
    return update_product_master(
        _tenant_id(),
        product_code, name, storage_type,
        conn=conn
    )


def update_driver_scoped(*, driver_id, name, hourly_drive_wage, hourly_load_wage, conn=None):
    return update_driver(
        _tenant_id(),
        driver_id, name, hourly_drive_wage, hourly_load_wage,
        conn=conn
    )


def update_vehicle_scoped(*, vehicle_id, name, mpg, 
                          purchase_price, yearly_mileage, salvage_value,
                          annual_insurance_cost,
                          annual_maintenance_cost, max_weight_lbs, max_volume_cubic_ft, storage_type,
                          conn=None):
    return update_vehicle(
        _tenant_id(),
        vehicle_id, name, mpg, 
        purchase_price, yearly_mileage, salvage_value,
        annual_insurance_cost,
        annual_maintenance_cost, max_weight_lbs, max_volume_cubic_ft, storage_type,
        conn=conn
    )


def update_entity_scoped(*, entity_id, name, entity_min_profit, conn=None):
    return update_entity(
        _tenant_id(),
        entity_id, name, entity_min_profit,
        conn=conn
    )


def update_supply_scoped(*, supply_id, entity_id, location_id, product_code, quantity_available,
                         unit_weight_lbs, unit_volume_cu_ft, items_per_handling_unit, cost_per_item,
                         conn=None):
    return update_supply(
        _tenant_id(),
        supply_id, entity_id, location_id, product_code, quantity_available,
        unit_weight_lbs, unit_volume_cu_ft, items_per_handling_unit, cost_per_item,
        conn=conn
    )


def update_demand_scoped(*, demand_id, location_id, product_code, quantity_needed, max_price, conn=None):
    return update_demand(
        _tenant_id(),
        demand_id, location_id, product_code, quantity_needed, max_price,
        conn=conn
    )


def update_route_scoped(*, route_id, name, origin_location_id, dest_location_id, conn=None):
    return update_route(
        _tenant_id(),
        route_id, name, origin_location_id, dest_location_id,
        conn=conn
    )


def update_scenario_scoped(*, scenario_id, route_id, vehicle_id, driver_id, run_date,
                           snapshot_driver_wage, snapshot_driver_load_wage,
                           snapshot_vehicle_mpg, snapshot_gas_price,
                           snapshot_depreciation_per_mile,
                           snapshot_daily_insurance, snapshot_daily_maintenance_cost,
                           snapshot_planned_load_minutes, snapshot_planned_unload_minutes,
                           actual_load_minutes, actual_unload_minutes, snapshot_total_revenue,
                           conn=None):
    return update_scenario(
        _tenant_id(),
        scenario_id, route_id, vehicle_id, driver_id, run_date,
        snapshot_driver_wage, snapshot_driver_load_wage,
        snapshot_vehicle_mpg, snapshot_gas_price,
        snapshot_depreciation_per_mile,
        snapshot_daily_insurance, snapshot_daily_maintenance_cost,
        snapshot_planned_load_minutes, snapshot_planned_unload_minutes,
        actual_load_minutes, actual_unload_minutes, snapshot_total_revenue,
        conn=conn
    )


def update_manifest_item_scoped(*, manifest_item_id, scenario_id, item_name, quantity_loaded,
                                supply_id=None, demand_id=None,
                                snapshot_cost_per_item=0.0, snapshot_items_per_unit=1,
                                snapshot_unit_weight=0.0, snapshot_unit_volume=0.0,   
                                snapshot_price_per_item=0.0,
                                conn=None):
    return update_manifest_item(
        _tenant_id(),
        manifest_item_id, scenario_id, item_name, quantity_loaded,
        supply_id, demand_id,
        snapshot_cost_per_item, snapshot_items_per_unit,
        snapshot_unit_weight, snapshot_unit_volume,
        snapshot_price_per_item,
        conn=conn
    )