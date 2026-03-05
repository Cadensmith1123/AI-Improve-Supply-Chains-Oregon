from flask import g
from db.functions.connect import get_db
from db.functions.tennant_functions import scoped_read as read, scoped_create as create, scoped_update as update, scoped_delete as delete
from decimal import Decimal #used to combat floating point errors
from datetime import date


def _get_tenant_id():
    return g.get('tenant_id', 1)

def get_locations(conn=None):
    location_data = read.view_locations_scoped(conn=conn, columns=['location_id', 'name'])
    return location_data


def _to_int(x):
    return int(x) if x not in (None, "") else None


def _to_dec(x):
    return Decimal(str(x)) if x not in (None, "") else None


def create_scenario(
        route_id,
        total_revenue,
        vehicle_id = None,
        driver_id = None,
        run_date = None,
        current_gas_price = None,
        depreciation = None,
        daily_insurance = None,
        daily_maintenance = None,
        conn = None
        ):
    """
    Creates new scenario header can take string int or float as inputs. 
    
    :param route_id: route ID (required)
    :param total_revenue: total revenue (required)
    :param vehicle_id: vehicle id (optional)
    :param driver_id: driver id (optional)
    :param run_date: run date (optional defaults to current date)
    :param current_gas_price: gas price (optional)
    :param depreciation: calculated depreciation per mile (optional)
    :param daily_insurance: calculated daily insurance cost (optional)
    :param daily_maintenance: calculated daily maintenance cost (optional)

    Returns the ID of the newly created scenario. 
    """
    if route_id is None:
        raise ValueError("route_id is required")
    if total_revenue is None:
        raise ValueError("total_revenue is required")

    tenant_id = _get_tenant_id()
    route_id = int(route_id)
    vehicle_id = _to_int(vehicle_id)
    driver_id = _to_int(driver_id)
    total_revenue = _to_dec(total_revenue)
    current_gas_price = _to_dec(current_gas_price)
    depreciation = _to_dec(depreciation)
    daily_insurance = _to_dec(daily_insurance)
    daily_maintenance = _to_dec(daily_maintenance)

    if current_gas_price is None:
        current_gas_price = Decimal("0.0")
        
    if depreciation is None:
        depreciation = Decimal("0.0")
    if daily_insurance is None:
        daily_insurance = Decimal("0.0")
    if daily_maintenance is None:
        daily_maintenance = Decimal("0.0")

    if run_date in ("", None):
        run_date = date.today()

    should_close = False
    if conn is None:
        conn = get_db()
        should_close = True
    
    if conn is None:
        raise RuntimeError("Failed to connect to database")

    try:
        cur = conn.cursor()

        args = [
            tenant_id,
            route_id,
            vehicle_id,
            driver_id,
            run_date,
            current_gas_price,
            total_revenue,
            depreciation,
            daily_insurance,
            daily_maintenance,
            0
        ]
        result = cur.callproc("create_trip_header", args)
        conn.commit()
        cur.close()
    finally:
        if should_close and conn:
            conn.close()

    new_scenario_id = result[-1]

    return new_scenario_id


def update_scenario(
    scenario_id,
    route_id=None,
    total_revenue=None,
    vehicle_id=None,
    driver_id=None,
    run_date=None,
    current_gas_price=None,
    depreciation=None,
    daily_insurance=None,
    daily_maintenance=None,
    conn=None
):
    """
    :param scenario_id: Scenario id (required)
    :param route_id: Route id (optional)
    :param total_revenue: total_revenue (optional)
    :param vehicle_id: vehicle id (optional)
    :param driver_id: driver id (optional)
    :param run_date: run date (optional)
    :param current_gas_price: gas price (optional)
    :param depreciation: calculated depreciation per mile (optional)
    :param daily_insurance: calculated daily insurance cost (optional)
    :param daily_maintenance: calculated daily maintenance cost (optional)
    """
    should_close = False
    if conn is None:
        conn = get_db()
        should_close = True
    
    if conn is None:
        raise RuntimeError("Failed to connect to database")

    tenant_id = _get_tenant_id()
    try:
        cur = conn.cursor(dictionary=True)

        args = [
            tenant_id,
            int(scenario_id),
            _to_int(route_id),
            _to_int(vehicle_id),
            _to_int(driver_id),
            run_date if run_date not in (None, "") else None,
            _to_dec(current_gas_price),
            _to_dec(total_revenue),
            _to_dec(depreciation) if depreciation is not None else None,
            _to_dec(daily_insurance) if daily_insurance is not None else None,
            _to_dec(daily_maintenance) if daily_maintenance is not None else None
        ]

        cur.callproc("update_trip_header", args)

        rows = []
        for r in cur.stored_results():
            rows.extend(r.fetchall())
        conn.commit()
        cur.close()
        return rows[0] if rows else None
    finally:
        if should_close and conn:
            conn.close()


def refresh_scenario(scenario_id, depreciation, daily_insurance, daily_maintenance, conn=None):
    """
    Updates snapshot values in the scenario header. 
    Requires depreciation, insurance, and maintenance to be passed in (calculated by frontend).
    """
    should_close = False
    if conn is None:
        conn = get_db()
        should_close = True
    
    if conn is None:
        raise RuntimeError("Failed to connect to database")

    tenant_id = _get_tenant_id()
    try:
        cur = conn.cursor()
        cur.callproc("refresh_trip_snapshots", [tenant_id, scenario_id, depreciation, daily_insurance, daily_maintenance])
        conn.commit()
        cur.close()
        return True
    finally:
        if should_close and conn:
            conn.close()


def add_manifest_items(
        scenario_id,
        item_name,
        quantity_loaded,
        supply_id = None,
        demand_id = None,
        cost_per_item = None,
        items_per_unit = None,
        unit_weight_lbs = None,
        unit_volume = None,
        price_per_item = None,
        conn = None
):
    """
    adds a product to the trip manifest
    
    :param scenario_id: scenario id (required)
    :param item_name: name of item (required)
    :param quantity_loaded: quantity loaded (handling units, required)
    :param supply_id: supply id (optional)
    :param demand_id: demand id (optional)
    :param cost_per_item: cost per item (optional)
    :param items_per_unit: items per handling unit (optional)
    :param unit_weight_lbs: weight per handling unit (optional)
    :param price_per_item: sale price per item (optional)
    """
    return create.add_manifest_item_scoped(
        scenario_id=scenario_id,
        item_name=item_name,
        quantity_loaded=quantity_loaded,
        supply_id=supply_id,
        demand_id=demand_id,
        snapshot_cost_per_item=cost_per_item,
        snapshot_items_per_unit=items_per_unit,
        snapshot_unit_weight=unit_weight_lbs,
        snapshot_unit_volume=unit_volume,
        snapshot_price_per_item=price_per_item,
        conn=conn
    )

def update_manifest_item(
        manifest_item_id,
        scenario_id,
        item_name,
        quantity_loaded,
        cost_per_item=None,
        items_per_unit=None,
        unit_weight=None,
        unit_volume=None,
        price_per_item=None,
        conn=None
):
    """
    Updates an existing manifest item.
    """
    return update.update_manifest_item_scoped(
        manifest_item_id=manifest_item_id,
        scenario_id=scenario_id,
        item_name=item_name,
        quantity_loaded=quantity_loaded,
        snapshot_cost_per_item=cost_per_item,
        snapshot_items_per_unit=items_per_unit,
        snapshot_unit_weight=unit_weight,
        snapshot_unit_volume=unit_volume,
        snapshot_price_per_item=price_per_item,
        conn=conn
    )

def remove_manifest_item(manifest_item_id, conn=None):
    """
    Removes an item from the manifest.
    """
    return delete.delete_manifest_item_scoped(
        manifest_item_id=manifest_item_id,
        conn=conn
    )

def _safe_dec(val, default="0"):
    """Helper to safely convert values to Decimal, handling None."""
    return Decimal(str(val)) if val is not None else Decimal(default)


def get_complete_route_details(scenario_id, conn=None):
    """
    Optimized fetch that gets header, route def, locations, and items in one go.
    Solves N+1 problem.
    """
    if scenario_id in (None, ""):
        raise ValueError("scenario_id is required")
    scenario_id = int(scenario_id)

    should_close = False
    if conn is None:
        conn = get_db()
        should_close = True
    
    if conn is None:
        raise RuntimeError("Failed to connect to database")

    tenant_id = _get_tenant_id()
    try:
        cur = conn.cursor(dictionary=True)
        cur.callproc("get_complete_route_details", [tenant_id, scenario_id])
        
        # Expecting 2 result sets: Header (row 0) and Items (rows 1..N)
        result_sets = [r.fetchall() for r in cur.stored_results()]
        cur.close()
        
        return result_sets
    finally:
        if should_close and conn:
            conn.close()