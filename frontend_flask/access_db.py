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

def _calculate_route_internals(header, items):
    """
    Centralized logic to enrich manifest and calculate full trip costs.
    Returns (enriched_manifest, costs_dict).
    """
    manifest = _enrich_manifest_items(items)
    totals = {
        "total_cogs": round(sum(m['line_cogs'] for m in manifest), 2),
        "calculated_revenue": round(sum(m['line_total'] for m in manifest), 2),
        "total_weight_lbs": round(sum(m['line_weight'] for m in manifest), 2),
        "total_volume": round(sum(m['line_volume'] for m in manifest), 2)
    }
    costs = logic.calculate_trip_costs(header, items, totals)
    return manifest, costs

def _calculate_vehicle_costs(vehicle_id):
    """
    Helper to calculate depreciation, insurance, and maintenance for a vehicle
    based on the standard trip length.
    Returns (depreciation, daily_insurance, daily_maintenance) or (None, None, None).
    """
    if not vehicle_id:
        return None, None, None
    v = get_vehicle(vehicle_id)
    if not v:
        return None, None, None
    miles, _ = logic.get_trip_length()
    return logic.calculate_operating_costs(v, miles)

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
    # Use optimized fetch for all scenarios
    scenarios = read.view_scenarios_scoped()
    out = []
    for s in scenarios:
        # Reuse the optimized complete fetch
        result_sets = scenario_management.get_complete_route_details(s['scenario_id'])
        if result_sets and result_sets[0]:
            header = result_sets[0][0]
            items = result_sets[1]
            _, costs = _calculate_route_internals(header, items)
            out.append(costs)
    return out


def get_route_raw(route_id):
    result_sets = scenario_management.get_complete_route_details(route_id)

    if result_sets and result_sets[0]:
        header = result_sets[0][0]
        items = result_sets[1]
        manifest, costs = _calculate_route_internals(header, items)
        d = {'header': header, 'items': items, 'manifest': manifest}
        d['costs'] = costs
        return d
    return None


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

        scenarios = read.view_scenarios_scoped()
        for s in scenarios:
            if s.get('vehicle_id') == vehicle_id:
                dep, ins, maint = _calculate_vehicle_costs(vehicle_id)
                scenario_management.refresh_scenario(s.get('scenario_id'), dep or 0.0, ins or 0.0, maint or 0.0)

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

def _map_scenario_to_route_view(scenario, route_def):
    """
    Helper to map DB scenario/route to frontend list view structure.
    
    Returns:
        dict: A dictionary containing route summary data for the list view.
    """
    return {
        "route_id": scenario.get('scenario_id'), 
        "run_date": scenario.get('run_date'),
        "name": route_def.get('name') if route_def else "Unknown Route",
        "origin_location_id": route_def.get('origin_location_id') if route_def else None,
        "dest_location_id": route_def.get('dest_location_id') if route_def else None,
        "sales_amount": logic.safe_float(scenario.get('snapshot_total_revenue')),
        "entered_revenue": logic.safe_float(scenario.get('snapshot_total_revenue')),
        "vehicle_id": scenario.get('vehicle_id'),
        "driver_id": scenario.get('driver_id'),
        "driver_cost": logic.safe_float(scenario.get('snapshot_driver_wage')),
        "load_cost": logic.safe_float(scenario.get('snapshot_driver_load_wage')),
        "unload_cost": logic.safe_float(scenario.get('snapshot_driver_load_wage')),
        "fuel_cost": 0.0,
        "depreciation_cost": 0.0,
        "insurance_cost": logic.safe_float(scenario.get('snapshot_daily_insurance')),
        "gas_price": logic.safe_float(scenario.get('snapshot_gas_price')),
    }

def list_routes():
    """
    Does a 'join' in python between routes (name, origin, destination) and 
    scenario (financial, and date specific information)
    
    Returns:
        List[dict]: A list of dictionaries, where each dictionary represents a route 
                    prepared for the frontend list view.
    """
    scenarios = read.view_scenarios_scoped()
    if not scenarios:
        return []

    all_routes = read.view_routes_scoped()
    routes_map = {r['route_id']: r for r in all_routes}

    return [_map_scenario_to_route_view(s, routes_map.get(s.get('route_id'))) for s in scenarios]



def get_route(route_id: int):
    """
    Fetches and calculates all details for a specific route.

    Returns:
        dict: A dictionary containing the full route view (header, enriched manifest, 
              calculated costs, and UI aliases), or None if the route does not exist.
    """
    result_sets = scenario_management.get_complete_route_details(route_id)

    if not result_sets or not result_sets[0]:
        return None

    header = result_sets[0][0]
    items = result_sets[1]
    
    manifest, costs = _calculate_route_internals(header, items)

    # Start with raw header data
    route_view = header.copy()
    
    # Merge in calculated costs
    route_view.update(costs)

    # Frontend-specific aliases and formatting
    route_view.update({
        "route_id": route_id,
        "name": header.get('route_name'), # Frontend expects 'name'
        "origin_address": f"{header.get('origin_address_street')} {header.get('origin_city')} {header.get('origin_state')}",
        "dest_address": f"{header.get('dest_address_street')} {header.get('dest_city')} {header.get('dest_state')}",
        "items": items,
        "manifest": manifest,
        "sales_amount": logic.safe_float(header.get('entered_revenue')),
        "base_sales_amount": logic.safe_float(header.get('entered_revenue')),
        
        # Map DB column names to Form field names
        "driver_cost": logic.safe_float(header.get('driver_drive_rate')),
        "load_cost": logic.safe_float(header.get('driver_load_rate')),
        "unload_cost": logic.safe_float(header.get('driver_load_rate')),
        "insurance_cost": logic.safe_float(header.get('daily_insurance')),
        
        # Calculated Aggregates (Aliases for UI)
        "calc_driver_cost": logic.safe_float(costs.get('driver_cost_total_est')),
        "calc_fuel_cost": logic.safe_float(costs.get('fuel_cost_est')),
        "calc_cogs": logic.safe_float(costs.get('total_cogs')),
        "calc_total_cost": logic.safe_float(costs.get('total_cost')),
        "calc_vehicle_cost": (
            logic.safe_float(costs.get('depreciation_cost_est')) + 
            logic.safe_float(costs.get('daily_insurance')) + 
            logic.safe_float(costs.get('daily_maintenance_cost'))
        ),
    })

    return route_view


def get_dashboard_data():
    """
    Aggregates all data needed for the main routes dashboard.
    Enriches routes with calculated costs, manifest items, and resolved names.

    Returns:
        dict: A dictionary containing:
            - "routes": List[dict] of route summaries with calculated costs.
            - "locations": List[dict] of available locations.
            - "vehicles": List[dict] of available vehicles.
            - "products": List[dict] of available products.
            - "drivers": List[dict] of available drivers.
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
    sales_amount: float,
    vehicle_id: Optional[int],
    driver_id: Optional[int],
    gas_price: Optional[float]
):
    """
    Creates a new route definition and its associated financial scenario.
    """
    depreciation, daily_insurance, daily_maintenance = _calculate_vehicle_costs(vehicle_id)

    try:
        real_route_id = create.add_route_scoped(
            name=name,
            origin_location_id=origin_location_id,
            dest_location_id=dest_location_id
        )
        
        scenario_id = scenario_management.create_scenario(
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
    sales_amount: float,
    vehicle_id: Optional[int] = None,
    driver_id: Optional[int] = None,
):
    """
    Updates an existing route's definition and financial scenario.
    """
    depreciation, daily_insurance, daily_maintenance = _calculate_vehicle_costs(vehicle_id)

    try:
        scenario_management.update_scenario(
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
    """
    Recalculates vehicle-related costs (depreciation, insurance, maintenance) 
    for a route based on its assigned vehicle and updates the snapshot.
    """
    try:
        scenarios = read.view_scenarios_scoped(ids=route_id)
        if not scenarios:
            return False, "Scenario not found"

        vehicle_id = scenarios[0].get('vehicle_id')
        dep, ins, maint = _calculate_vehicle_costs(vehicle_id)

        # If no vehicle, default costs to 0.0
        scenario_management.refresh_scenario(route_id, dep or 0.0, ins or 0.0, maint or 0.0)
        return True, None
    except Exception as e:
        return False, str(e)
    
# =============================================================================
# ROUTE/SCENARIO ASSET MANAGEMENT
# =============================================================================


def assign_vehicle_to_route(route_id: int, vehicle_id: Optional[int]):
    depreciation, daily_insurance, daily_maintenance = _calculate_vehicle_costs(vehicle_id)

    try:
        scenario_management.update_scenario(
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
    try:
        scenario_management.update_scenario(
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
    result_sets = scenario_management.get_complete_route_details(route_id)

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
    prod = get_product(product_id)
    if not prod:
        return False, "Product not found"
    
    # Optimization: Fetch raw items directly to avoid overhead of calculating costs
    # just to check for existence.
    result_sets = scenario_management.get_complete_route_details(route_id)
    items = result_sets[1] if result_sets and len(result_sets) > 1 else []

    existing_item = next((i for i in items if str(i.get('product_id')) == str(product_id)), None)

    if existing_item:
        try:
            scenario_management.update_manifest_item(
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

    result_sets = scenario_management.get_complete_route_details(route_id)
    items = result_sets[1] if result_sets and len(result_sets) > 1 else []

    item_to_delete = None
    for item in items:
        if str(item.get('product_id')) == target_code:
            item_to_delete = item.get('manifest_item_id')
            break
    
    if item_to_delete:
        try:
            scenario_management.remove_manifest_item(manifest_item_id=item_to_delete)
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
        "profit_est_entered", "profit_est_calculated", "margin_est_entered", "margin_est_calculated",
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
        "profit_est_entered", "profit_est_calculated", "margin_est_entered", "margin_est_calculated",
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
    enriched_items = details.get('manifest', [])
        
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
