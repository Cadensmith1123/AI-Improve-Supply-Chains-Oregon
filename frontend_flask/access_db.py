from flask import g
from typing import Optional
from db.functions.tennant_functions import (
    scoped_read as read, 
    scoped_create as create, 
    scoped_update as update, 
    scoped_delete as delete
)
import logic
from db.functions import scenario_management

# =============================================================================
# HELPERS
# =============================================================================


def _get_tenant_id():
    """Helper to get tenant_id safely from Flask global context."""
    return g.get('tenant_id', 1)


def _enrich_manifest_items(items):
    """
    Maps raw DB manifest items to frontend structure and calculates metrics.
    Handles price fallback to product master if snapshot is missing.
    """
    out = []
    for i in items:
        # Fallback logic: if snapshot price is missing, look up product master
        p = None
        if i.get('price_per_item') is None and i.get('unit_price') is None:
             p = get_product(i['product_id'])

        metrics = logic.calculate_manifest_item_metrics(i, p)

        out.append({
            "manifest_item_id": i.get('manifest_item_id'),
            "product_id": i.get('product_id'), 
            "product_name": i.get('product_name'),
            "quantity": metrics['quantity'],
            "unit_price": metrics['unit_price'],
            "items_per_unit": metrics['items_per_unit'],
            "cost_per_item": i.get('cost_per_item'),
            "unit_weight": i.get('unit_weight_lbs'),
            "unit_volume": i.get('unit_volume'),
            # Enriched metrics
            "line_total": metrics['line_total'],
            "line_cogs": metrics['line_cogs'],
            "line_weight": metrics['line_weight'],
            "line_volume": metrics['line_volume']
        })
    
    out.sort(key=lambda x: x["product_name"].lower())
    return out

# =============================================================================
# CREATE
# =============================================================================


def create_location(
    name: str, 
    loc_type: str = "Hub",
    address: str = "",
    city: str = "",
    state: str = "",
    zip_code: str = "",
    phone: str = "",
    avg_load_minutes: str = "30",
    avg_unload_minutes: str = "30"
):
    try:
        new_id = create.add_location_scoped(
            name=name,
            type=loc_type,
            address_street=address,
            city=city,
            state=state,
            zip_code=zip_code,
            phone=phone,
            latitude=0.0,
            longitude=0.0,
            avg_load_minutes=logic.safe_int(avg_load_minutes, 30),
            avg_unload_minutes=logic.safe_int(avg_unload_minutes, 30)
        )
        return True, None, new_id
    except Exception as e:
        return False, str(e), None


def create_driver(name: str, hourly_drive_wage: str, hourly_load_wage: str):
    try:
        new_id = create.add_driver_scoped(
            name=name,
            hourly_drive_wage=logic.safe_float(hourly_drive_wage),
            hourly_load_wage=logic.safe_float(hourly_load_wage)
        )
        return True, None, new_id
    except Exception as e:
        return False, str(e), None


def create_vehicle(
    vehicle_name: str, 
    mpg: str, 
    capacity: str, 
    purchase_price: str = None, 
    yearly_mileage: str = None, 
    salvage_value: str = None,
    insurance_cost: str = None,
    maintenance_cost: str = None,
    storage_type: str = "Dry"
):
    try:
        cap_val = logic.parse_capacity_string(capacity)

        new_id = create.add_vehicle_scoped(
            name=vehicle_name,
            mpg=logic.safe_float(mpg, 10.0),
            purchase_price=logic.safe_float(purchase_price),
            yearly_mileage=logic.safe_float(yearly_mileage),
            salvage_value=logic.safe_float(salvage_value),
            annual_insurance_cost=logic.safe_float(insurance_cost),
            annual_maintenance_cost=logic.safe_float(maintenance_cost),
            max_weight_lbs=cap_val,
            max_volume_cubic_ft=1000,
            storage_type=storage_type
        )
        return True, None, new_id
    except Exception as e:
        return False, str(e), None


def create_product(product_name: str, sku: str, storage_type: str):
    try:
        new_id = create.add_product_master_scoped(
            product_code=sku,
            name=product_name,
            storage_type=storage_type if storage_type else "Dry"
        )
        return True, None, new_id
    except Exception as e:
        return False, str(e), None

# =============================================================================
# VIEW
# =============================================================================


def list_locations():
    return read.view_locations_scoped()


def list_drivers():
    return read.view_drivers_scoped()


def get_driver(driver_id: int):
    rows = read.view_drivers_scoped(ids=driver_id)
    if rows:
        return rows[0]
    return None


def list_vehicles():
    rows = read.view_vehicles_scoped()
    for r in rows:
        r['vehicle_name'] = r.get('name')
    return rows


def get_vehicle(vehicle_id: int):
    rows = read.view_vehicles_scoped(ids=vehicle_id)
    if rows:
        rows[0]['vehicle_name'] = rows[0].get('name')
        return rows[0]
    return None


def get_all_routes_raw():
    tid = _get_tenant_id()
    # Use optimized fetch for all scenarios
    scenarios = read.view_scenarios_scoped()
    out = []
    for s in scenarios:
        # Reuse the optimized complete fetch
        result_sets = scenario_management.get_complete_route_details(tid, s['scenario_id'])
        if result_sets and result_sets[0]:
            header = result_sets[0][0]
            items = result_sets[1]
            costs = logic.calculate_trip_costs(header, items)
            out.append(costs)
    return out


def get_route_raw(route_id):
    tid = _get_tenant_id()
    result_sets = scenario_management.get_complete_route_details(tid, route_id)

    if result_sets and result_sets[0]:
        header = result_sets[0][0]
        items = result_sets[1]
        d = {'header': header, 'items': items}
        costs = logic.calculate_trip_costs(d['header'], d['items'])
        d['costs'] = costs
    return d


def list_products():
    rows = read.view_products_master_scoped()
    for r in rows:
        r['product_name'] = r.get('name')
        r['product_id'] = r.get('product_code')
    return rows


def get_product(product_id):
    rows = read.view_products_master_scoped(ids=product_id)
    if rows:
        rows[0]['product_name'] = rows[0].get('name')
        rows[0]['product_id'] = rows[0].get('product_code')
        return rows[0]
    return None

# =============================================================================
# UPDATE
# =============================================================================


def update_location(
    location_id: int, 
    name: str, 
    loc_type: str = "Hub",
    address: str = "",
    city: str = "",
    state: str = "",
    zip_code: str = "",
    phone: str = "",
    avg_load_minutes: str = "30",
    avg_unload_minutes: str = "30"
):
    try:
        update.update_location_scoped(
            location_id=location_id,
            name=name,
            type=loc_type,
            address_street=address,
            city=city,
            state=state,
            zip_code=zip_code,
            phone=phone,
            latitude=0.0,
            longitude=0.0,
            avg_load_minutes=logic.safe_int(avg_load_minutes, 30),
            avg_unload_minutes=logic.safe_int(avg_unload_minutes, 30)
        )
        return True, None
    except Exception as e:
        return False, str(e)


def update_driver(driver_id: int, name: str, hourly_drive_wage: str, hourly_load_wage: str):
    try:
        update.update_driver_scoped(
            driver_id=driver_id,
            name=name,
            hourly_drive_wage=logic.safe_float(hourly_drive_wage),
            hourly_load_wage=logic.safe_float(hourly_load_wage)
        )
        return True, None
    except Exception as e:
        return False, str(e)


def update_vehicle(
    vehicle_id: int, 
    vehicle_name: str, 
    mpg: str, 
    capacity: str,
    purchase_price: str = None, 
    yearly_mileage: str = None, 
    salvage_value: str = None,
    insurance_cost: str = None,
    maintenance_cost: str = None,
    storage_type: str = "Dry"
):
    try:
        cap_val = logic.parse_capacity_string(capacity)

        update.update_vehicle_scoped(
            vehicle_id=vehicle_id,
            name=vehicle_name,
            mpg=logic.safe_float(mpg, 10.0),
            purchase_price=logic.safe_float(purchase_price),
            yearly_mileage=logic.safe_float(yearly_mileage),
            salvage_value=logic.safe_float(salvage_value),
            annual_insurance_cost=logic.safe_float(insurance_cost),
            annual_maintenance_cost=logic.safe_float(maintenance_cost),
            max_weight_lbs=cap_val,
            max_volume_cubic_ft=1000,
            storage_type=storage_type
        )

        tid = _get_tenant_id() # Needed for scenario_management
        scenarios = read.view_scenarios_scoped()
        for s in scenarios:
            if s.get('vehicle_id') == vehicle_id:
                scenario_management.refresh_scenario(tid, s.get('scenario_id'))

        return True, None
    except Exception as e:
        return False, str(e)


def update_product(product_id: str, product_name: str, storage_type: str):
    try:
        update.update_product_master_scoped(
            product_code=product_id,
            name=product_name,
            storage_type=storage_type if storage_type else "Dry"
        )
        return True, None
    except Exception as e:
        return False, str(e)

# =============================================================================
# DELETE
# =============================================================================


def delete_location(location_id: int):
    try:
        delete.delete_location_scoped(location_id=location_id)
        return True, None
    except Exception as e:
        if "foreign key constraint fails" in str(e).lower():
            return False, "Cannot delete location: It is used as an origin or destination in one or more routes."
        return False, str(e)


def delete_driver(driver_id: int):
    try:
        delete.delete_driver_scoped(driver_id=driver_id)
        return True, None
    except Exception as e:
        if "foreign key constraint fails" in str(e).lower():
            return False, "Cannot delete driver: They are assigned to one or more routes."
        return False, str(e)


def delete_vehicle(vehicle_id: int):
    try:
        delete.delete_vehicle_scoped(vehicle_id=vehicle_id)
        return True, None
    except Exception as e:
        if "foreign key constraint fails" in str(e).lower():
            return False, "Cannot delete vehicle: It is assigned to one or more routes."
        return False, str(e)


def delete_route(route_id: int):
    try:
        delete.delete_plan_scoped(scenario_id=route_id)
        return True, None
    except Exception as e:
        return False, str(e)


def delete_product(product_code: str):
    try:
        delete.delete_product_master_scoped(product_code=product_code)
        return True, None
    except Exception as e:
        if "foreign key constraint fails" in str(e).lower():
            return False, "Cannot delete product: It is present on one or more route manifests."
        return False, str(e)

# =============================================================================
# SCENARIO/ROUTE MANAGEMENT AND PYTHON 'JOINS'
# Potential for future optimization database side
# =============================================================================


def list_routes():
    """
    Does a 'join' in python between routes (name, origin, destination) and 
    scenario (financial, and date specific information)

    This could later be optimized using sql procedures but currently done in
    python for modularity. 
    """
    scenarios = read.view_scenarios_scoped()
    if not scenarios:
        return []

    all_routes = read.view_routes_scoped()
    routes_map = {r['route_id']: r for r in all_routes}

    out = []
    for s in scenarios:
        r_def = routes_map.get(s.get('route_id'))

        item = {
            "route_id": s.get('scenario_id'), 
            "run_date": s.get('run_date'),
            "name": r_def.get('name') if r_def else "Unknown Route",
            "origin_location_id": r_def.get('origin_location_id') if r_def else None,
            "dest_location_id": r_def.get('dest_location_id') if r_def else None,
            "sales_amount": logic.safe_float(s.get('snapshot_total_revenue')),
            "entered_revenue": logic.safe_float(s.get('snapshot_total_revenue')),
            "vehicle_id": s.get('vehicle_id'),
            "driver_id": s.get('driver_id'),
            "driver_cost": logic.safe_float(s.get('snapshot_driver_wage')),
            "load_cost": logic.safe_float(s.get('snapshot_driver_load_wage')),
            "unload_cost": logic.safe_float(s.get('snapshot_driver_load_wage')),
            "fuel_cost": 0.0,
            "depreciation_cost": 0.0,
            "insurance_cost": logic.safe_float(s.get('snapshot_daily_insurance')),
            "gas_price": logic.safe_float(s.get('snapshot_gas_price')),
        }
        out.append(item)
    return out


def get_route(route_id: int):
    tid = _get_tenant_id()

    result_sets = scenario_management.get_complete_route_details(tid, route_id)

    if not result_sets or not result_sets[0]:
        return None

    header = result_sets[0][0]
    items = result_sets[1]

    start_address = f"{header.get('origin_address_street')} {header.get('origin_city')} {header.get('origin_state')}"
    dest_address = f"{header.get('dest_address_street')} {header.get('dest_city')} {header.get('dest_state')}"

    # Enrich items first (handles price fallback and line totals)
    manifest = _enrich_manifest_items(items)

    # Calculate totals from the enriched manifest to ensure consistency
    totals = {
        "total_cogs": round(sum(m['line_cogs'] for m in manifest), 2),
        "calculated_revenue": round(sum(m['line_total'] for m in manifest), 2),
        "total_weight_lbs": round(sum(m['line_weight'] for m in manifest), 2),
        "total_volume": round(sum(m['line_volume'] for m in manifest), 2)
    }

    costs = logic.calculate_trip_costs(header, items, totals)

    return {
        "route_id": route_id,
        "name": header.get('route_name'),
        "origin_location_id": header.get('origin_location_id'),
        "dest_location_id": header.get('dest_location_id'),
        "origin_address": start_address, 
        "dest_address": dest_address,
        "items": items,  # Return raw items so we don't need to fetch them again
        "manifest": manifest, # Now fully enriched
        "base_sales_amount": logic.safe_float(header.get('entered_revenue')),
        "sales_amount": logic.safe_float(header.get('entered_revenue')),
        "vehicle_id": header.get('vehicle_id'),
        "driver_id": header.get('driver_id'),
        "driver_name": header.get('driver_name'),
        "driver_cost": logic.safe_float(header.get('driver_drive_rate')),
        "load_cost": logic.safe_float(header.get('driver_load_rate')),
        "unload_cost": logic.safe_float(header.get('driver_load_rate')),
        "fuel_cost": logic.safe_float(costs.get('fuel_cost_est')), # Use calculated cost
        "depreciation_cost": 0.0,
        "insurance_cost": logic.safe_float(header.get('daily_insurance')),
        "gas_price": logic.safe_float(header.get('gas_price')),
        "calc_driver_cost": logic.safe_float(costs.get('driver_cost_total_est')),
        "calc_fuel_cost": logic.safe_float(costs.get('fuel_cost_est')),
        "calc_vehicle_cost": logic.safe_float(costs.get('depreciation_cost_est')) + logic.safe_float(costs.get('daily_insurance')) + logic.safe_float(costs.get('daily_maintenance_cost')),
        "calc_cogs": logic.safe_float(costs.get('total_cogs')),
        "calc_total_cost": logic.safe_float(costs.get('driver_cost_total_est')) + logic.safe_float(costs.get('fuel_cost_est')) + logic.safe_float(costs.get('depreciation_cost_est')) + logic.safe_float(costs.get('daily_insurance')) + logic.safe_float(costs.get('daily_maintenance_cost')) + logic.safe_float(costs.get('total_cogs')),
        
        "drive_minutes_est": costs.get("drive_minutes_est"),
        "load_minutes_plan": costs.get("load_minutes_plan"),
        "unload_minutes_plan": costs.get("unload_minutes_plan"),
        "driver_drive_rate_per_hr": costs.get("driver_drive_rate_per_hr"),
        "driver_load_rate_per_hr": costs.get("driver_load_rate_per_hr"),
        "daily_insurance": costs.get("daily_insurance"),
        "daily_maintenance_cost": costs.get("daily_maintenance_cost"),
        "depreciation_cost_est": costs.get("depreciation_cost_est"),
        "fuel_cost_est": costs.get("fuel_cost_est"),
        "driver_drive_cost_est": costs.get("driver_drive_cost_est"),
        "driver_load_cost_est": costs.get("driver_load_cost_est"),
        "driver_unload_cost_est": costs.get("driver_unload_cost_est"),
        "driver_cost_total_est": costs.get("driver_cost_total_est"),
        "line_item_count": costs.get("line_item_count"),
        "total_weight_lbs": costs.get("total_weight_lbs"),
        "total_volume": costs.get("total_volume"),
        "total_cogs": costs.get("total_cogs"),
        "entered_revenue": costs.get("entered_revenue"),
        "calculated_revenue": costs.get("calculated_revenue"),
        "profit_est_entered": costs.get("profit_est_entered"),
        "profit_est_calculated": costs.get("profit_est_calculated"),
        "margin_est_entered": costs.get("margin_est_entered"),
        "margin_est_calculated": costs.get("margin_est_calculated"),
        "run_date": costs.get("run_date"),
        "total_distance_miles": costs.get("total_distance_miles"),
    }

def get_dashboard_data():
    """
    Aggregates all data needed for the main routes dashboard.
    Enriches routes with calculated costs, manifest items, and resolved names.
    """
    routes = list_routes()
    locations = list_locations()
    vehicles = list_vehicles()
    products = list_products()
    drivers = list_drivers()

    locations_map = {l["location_id"]: l["name"] for l in locations}
    vehicles_map = {v["vehicle_id"]: v for v in vehicles}

    for r in routes:
        # Resolve Location Names
        r["origin_name"] = locations_map.get(r["origin_location_id"], f"#{r['origin_location_id']}")
        r["dest_name"] = locations_map.get(r["dest_location_id"], f"#{r['dest_location_id']}")

        # Fetch full route details (costs, manifest)
        # This calls get_route -> get_complete_route_details -> calculate_trip_costs
        full_route = get_route(r["route_id"])
        
        r["total_cost"] = full_route.get("calc_total_cost", 0.0) if full_route else 0.0
        r["manifest_items"] = []
        r["fuel_cost"] = 0.0
        r["depreciation_cost"] = 0.0
        r["manifest_count"] = 0
        r["item_revenue"] = 0.0

        if full_route:
            r["fuel_cost"] = full_route.get("fuel_cost", 0.0)
            r["depreciation_cost"] = full_route.get("depreciation_cost", 0.0)
            r["manifest_count"] = full_route.get("line_item_count", 0)
            
            manifest_subtotal = full_route.get("calculated_revenue", 0.0)
            r["item_revenue"] = manifest_subtotal
            
            # Add item revenue to base sales amount
            base_sales = r.get("sales_amount") or 0.0
            r["sales_amount"] = base_sales + manifest_subtotal
            
            r["manifest_items"] = full_route.get("manifest", [])

        # Resolve Vehicle Name
        vid = r.get("vehicle_id")
        r["vehicle_name"] = vehicles_map.get(vid, {}).get("vehicle_name") if vid else None

    return {
        "routes": routes,
        "locations": locations,
        "vehicles": vehicles,
        "products": products,
        "drivers": drivers
    }

def create_route(
    name: str,
    origin_location_id: int,
    dest_location_id: int,
    origin_address: str,
    dest_address: str,
    sales_amount: float,
    vehicle_id: Optional[int],
    driver_id: Optional[int],
    gas_price: Optional[float],
    driver_cost: Optional[float],
    load_cost: Optional[float],
    unload_cost: Optional[float],
    fuel_cost: Optional[float],
    depreciation_cost: Optional[float],
    insurance_cost: Optional[float],
):
    tid = _get_tenant_id()

    depreciation = 0.0
    daily_insurance = 0.0
    daily_maintenance = 0.0
    if vehicle_id:
        v = get_vehicle(vehicle_id)
        if v:
            miles, _ = logic.get_trip_length()
            depreciation, daily_insurance, daily_maintenance = logic.calculate_operating_costs(v, miles)

    try:
        real_route_id = create.add_route_scoped(
            name=name,
            origin_location_id=origin_location_id,
            dest_location_id=dest_location_id
        )
        
        scenario_id = scenario_management.create_scenario(
            tenant_id=tid,
            route_id=real_route_id,
            total_revenue=sales_amount,
            vehicle_id=vehicle_id,
            driver_id=driver_id,
            current_gas_price=logic.safe_float(gas_price, 4.50),
            depreciation=depreciation,
            daily_insurance=daily_insurance,
            daily_maintenance=daily_maintenance
        )
        return True, None, scenario_id
    except Exception as e:
        return False, str(e), None


def update_route(
    route_id: int,
    name: str,
    origin_location_id: int,
    dest_location_id: int,
    origin_address: str,
    dest_address: str,
    sales_amount: float,
    driver_cost: Optional[float],
    load_cost: Optional[float],
    unload_cost: Optional[float],
    fuel_cost: Optional[float],
    depreciation_cost: Optional[float],
    insurance_cost: Optional[float],
    vehicle_id: Optional[int] = None,
    driver_id: Optional[int] = None,
):
    tid = _get_tenant_id()

    depreciation = None
    daily_insurance = None
    daily_maintenance = None
    if vehicle_id:
        v = get_vehicle(vehicle_id)
        if v:
            miles, _ = logic.get_trip_length()
            depreciation, daily_insurance, daily_maintenance = logic.calculate_operating_costs(v, miles)

    try:
        scenario_management.update_scenario(
            tenant_id=tid,
            scenario_id=route_id,
            total_revenue=sales_amount,
            vehicle_id=vehicle_id,
            driver_id=driver_id,
            depreciation=depreciation,
            daily_insurance=daily_insurance,
            daily_maintenance=daily_maintenance
        )

        raw_scenarios = read.view_scenarios_scoped(ids=route_id)
        if raw_scenarios:
            real_route_id = raw_scenarios[0].get('route_id')
            update.update_route_scoped(
                route_id=real_route_id,
                name=name,
                origin_location_id=origin_location_id,
                dest_location_id=dest_location_id
            )

        return True, None
    except Exception as e:
        return False, str(e)


def recalculate_route_costs(route_id: int):
    tid = _get_tenant_id()
    try:
        scenarios = read.view_scenarios_scoped(ids=route_id)
        if not scenarios:
            return False, "Scenario not found"

        vehicle_id = scenarios[0].get('vehicle_id')

        depreciation = 0.0
        daily_insurance = 0.0
        daily_maintenance = 0.0
        if vehicle_id:
            v = get_vehicle(vehicle_id)
            if v:
                miles, _ = logic.get_trip_length()
                depreciation, daily_insurance, daily_maintenance = logic.calculate_operating_costs(v, miles)

        scenario_management.refresh_scenario(tid, route_id, depreciation, daily_insurance, daily_maintenance)
        return True, None
    except Exception as e:
        return False, str(e)
    
# =============================================================================
# ROUTE/SCENARIO ASSET MANAGEMENT
# =============================================================================


def assign_vehicle_to_route(route_id: int, vehicle_id: Optional[int]):
    tid = _get_tenant_id()

    depreciation = None
    daily_insurance = None
    daily_maintenance = None
    if vehicle_id:
        v = get_vehicle(vehicle_id)
        if v:
            miles, _ = logic.get_trip_length()
            depreciation, daily_insurance, daily_maintenance = logic.calculate_operating_costs(v, miles)

    try:
        scenario_management.update_scenario(
            tenant_id=tid,
            scenario_id=route_id,
            vehicle_id=vehicle_id,
            depreciation=depreciation,
            daily_insurance=daily_insurance,
            daily_maintenance=daily_maintenance
        )
        return True, None
    except Exception as e:
        return False, str(e)


def assign_driver_to_route(route_id: int, driver_id: Optional[int]):
    tid = _get_tenant_id()
    try:
        scenario_management.update_scenario(
            tenant_id=tid,
            scenario_id=route_id,
            driver_id=driver_id
        )
        return True, None
    except Exception as e:
        return False, str(e)

# =============================================================================
# MANIFEST MANAGEMENT
# =============================================================================


def get_route_manifest(route_id: int):
    """
    Fetches manifest items for a specific route using the optimized stored procedure.
    """
    tid = _get_tenant_id()
    result_sets = scenario_management.get_complete_route_details(tid, route_id)

    if not result_sets or len(result_sets) < 2:
        return []

    items = result_sets[1]

    return _enrich_manifest_items(items)


def add_product_to_route(
    route_id: int, 
    product_id, 
    quantity: float, 
    price_per_item: Optional[float] = None, 
    items_per_unit: Optional[float] = None,
    cost_per_item: Optional[float] = None,
    unit_weight: Optional[float] = None,
    unit_volume: Optional[float] = None):
    tid = _get_tenant_id()
    prod = get_product(product_id)
    if not prod:
        return False, "Product not found"
    
    manifest = get_route_manifest(route_id)
    existing_item = next((i for i in manifest if str(i['product_id']) == str(product_id)), None)

    if existing_item:
        try:
            update.update_manifest_item_scoped(
                manifest_item_id=existing_item['manifest_item_id'],
                scenario_id=route_id,
                item_name=prod['name'],
                quantity_loaded=quantity,
                snapshot_cost_per_item=cost_per_item,
                snapshot_items_per_unit=items_per_unit,
                snapshot_unit_weight=unit_weight,
                snapshot_unit_volume=unit_volume,
                snapshot_price_per_item=price_per_item
            )
            return True, None
        except Exception as e:
            return False, str(e)
    else:
        try:
            scenario_management.add_manifest_items(
                tenant_id=tid,
                scenario_id=route_id,
                item_name=prod['name'],
                quantity_loaded=quantity,
                cost_per_item=cost_per_item,
                price_per_item=price_per_item,
                items_per_unit=items_per_unit,
                unit_weight_lbs=unit_weight,
                unit_volume=unit_volume
            )
            return True, None
        except Exception as e:
            return False, str(e)


def remove_product_from_route(route_id: int, product_id):
    target_code = str(product_id)
    
    all_products = read.view_products_master_scoped()
    target_name = None
    for p in all_products:
        if str(p['product_code']) == target_code:
            target_name = p['name']
            break
    
    if not target_name:
        target_name = target_code
    
    # Optimization: Only fetch items for this route, not the entire table
    manifest = get_route_manifest(route_id)
    item_to_delete = None
    for item in manifest:
        if item.get('product_name') == target_name:
            item_to_delete = item.get('manifest_item_id')
            break
    
    if item_to_delete:
        try:
            delete.delete_manifest_item_scoped(manifest_item_id=item_to_delete)
            return True, None
        except Exception as e:
            return False, str(e)
            
    return False, "Item not found in manifest"

# =============================================================================
# CSV EXPORT
# =============================================================================


def export_routes_csv(details_list, output_handle):
    cols = [
        "scenario_id", "run_date", "route_name", 
        "origin_name", "dest_name", "total_distance_miles",
        "vehicle_name", "driver_name",
        "entered_revenue", "calculated_revenue", "total_cost", 
        "profit_est_entered", "margin_est_entered",
        "total_cogs", 
        "driver_cost_total_est", "fuel_cost_est", 
        "depreciation_cost_est", "daily_insurance", "daily_maintenance_cost",
        "driver_drive_cost_est", "driver_load_cost_est", "driver_unload_cost_est",
        "driver_drive_rate_per_hr", "driver_load_rate_per_hr", "gas_price",
        "total_weight_lbs", "total_volume", "line_item_count",
        "drive_minutes_est", "load_minutes_plan", "unload_minutes_plan"
    ]
    csv_str = logic.generate_csv_export(details_list, columns=cols)
    output_handle.write(csv_str)


def export_route_detailed_csv(details, output_handle):
    # 1. Route Summary (Header)
    costs = details.get('costs', {})
    
    summary_cols = [
        "scenario_id", "run_date", "route_name", 
        "origin_name", "dest_name", "total_distance_miles",
        "vehicle_name", "driver_name",
        "entered_revenue", "calculated_revenue", "total_cost", 
        "profit_est_entered", "margin_est_entered",
        "total_cogs", 
        "driver_cost_total_est", "fuel_cost_est", 
        "depreciation_cost_est", "daily_insurance", "daily_maintenance_cost",
        "driver_drive_cost_est", "driver_load_cost_est", "driver_unload_cost_est",
        "driver_drive_rate_per_hr", "driver_load_rate_per_hr", "gas_price",
        "total_weight_lbs", "total_volume", "line_item_count",
        "drive_minutes_est", "load_minutes_plan", "unload_minutes_plan"
    ]
    summary_csv = logic.generate_csv_export([costs], columns=summary_cols)
    
    output_handle.write("ROUTE_SUMMARY\n")
    output_handle.write(summary_csv)
    output_handle.write("\n")
    
    # 2. Manifest Items
    items = details.get('items', [])
    
    enriched_items = []
    for i in items:
        metrics = logic.calculate_manifest_item_metrics(i)
        row = i.copy()
        row.update(metrics)
        enriched_items.append(row)
        
    items_cols = [
        "product_name", "quantity", "items_per_unit", 
        "unit_price", "line_total", 
        "cost_per_item", "line_cogs",
        "unit_weight", "line_weight", 
        "unit_volume", "line_volume"
    ]
    items_csv = logic.generate_csv_export(enriched_items, columns=items_cols)
    output_handle.write("MANIFEST_ITEMS\n")
    output_handle.write(items_csv)
