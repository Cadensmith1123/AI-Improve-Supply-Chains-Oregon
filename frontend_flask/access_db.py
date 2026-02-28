from flask import g
from typing import Optional
from db.functions.tennant_functions import (
    scoped_read as read, 
    scoped_create as create, 
    scoped_update as update, 
    scoped_delete as delete
)
from db.functions import scenario_management

def _get_tenant_id():
    """Helper to get tenant_id safely from Flask global context."""
    return g.get('tenant_id', 1)

# --- Locations ---

def list_locations():
    return read.view_locations_scoped()

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
            avg_load_minutes=int(avg_load_minutes) if avg_load_minutes else 30,
            avg_unload_minutes=int(avg_unload_minutes) if avg_unload_minutes else 30
        )
        return True, None, new_id
    except Exception as e:
        return False, str(e), None

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
            avg_load_minutes=int(avg_load_minutes) if avg_load_minutes else 30,
            avg_unload_minutes=int(avg_unload_minutes) if avg_unload_minutes else 30
        )
        return True, None
    except Exception as e:
        return False, str(e)

def delete_location(location_id: int):
    try:
        delete.delete_location_scoped(location_id=location_id)
        return True, None
    except Exception as e:
        if "foreign key constraint fails" in str(e).lower():
            return False, "Cannot delete location: It is used as an origin or destination in one or more routes."
        return False, str(e)

# --- Drivers ---

def list_drivers():
    return read.view_drivers_scoped()

def get_driver(driver_id: int):
    rows = read.view_drivers_scoped(ids=driver_id)
    if rows:
        return rows[0]
    return None

def create_driver(name: str, hourly_drive_wage: str, hourly_load_wage: str):
    try:
        new_id = create.add_driver_scoped(
            name=name,
            hourly_drive_wage=float(hourly_drive_wage) if hourly_drive_wage else 0.0,
            hourly_load_wage=float(hourly_load_wage) if hourly_load_wage else 0.0
        )
        return True, None, new_id
    except Exception as e:
        return False, str(e), None

def update_driver(driver_id: int, name: str, hourly_drive_wage: str, hourly_load_wage: str):
    try:
        update.update_driver_scoped(
            driver_id=driver_id,
            name=name,
            hourly_drive_wage=float(hourly_drive_wage) if hourly_drive_wage else 0.0,
            hourly_load_wage=float(hourly_load_wage) if hourly_load_wage else 0.0
        )
        return True, None
    except Exception as e:
        return False, str(e)

def delete_driver(driver_id: int):
    try:
        delete.delete_driver_scoped(driver_id=driver_id)
        return True, None
    except Exception as e:
        if "foreign key constraint fails" in str(e).lower():
            return False, "Cannot delete driver: They are assigned to one or more routes."
        return False, str(e)

# --- Vehicles ---

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
        try:
            cap_val = float(capacity.split()[0])
        except (ValueError, IndexError, AttributeError):
            cap_val = 1000.0
        
        new_id = create.add_vehicle_scoped(
            name=vehicle_name,
            mpg=float(mpg) if mpg else 10.0,
            purchase_price=float(purchase_price) if purchase_price else 0.0,
            yearly_mileage=float(yearly_mileage) if yearly_mileage else 0.0,
            salvage_value=float(salvage_value) if salvage_value else 0.0,
            annual_insurance_cost=float(insurance_cost) if insurance_cost else 0.0,
            annual_maintenance_cost=float(maintenance_cost) if maintenance_cost else 0.0,
            max_weight_lbs=cap_val,
            max_volume_cubic_ft=1000,
            storage_type=storage_type
        )
        return True, None, new_id
    except Exception as e:
        return False, str(e), None

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
        try:
            cap_val = float(capacity.split()[0])
        except (ValueError, IndexError, AttributeError):
            cap_val = 1000.0
        
        update.update_vehicle_scoped(
            vehicle_id=vehicle_id,
            name=vehicle_name,
            mpg=float(mpg) if mpg else 10.0,
            purchase_price=float(purchase_price) if purchase_price else 0.0,
            yearly_mileage=float(yearly_mileage) if yearly_mileage else 0.0,
            salvage_value=float(salvage_value) if salvage_value else 0.0,
            annual_insurance_cost=float(insurance_cost) if insurance_cost else 0.0,
            annual_maintenance_cost=float(maintenance_cost) if maintenance_cost else 0.0,
            max_weight_lbs=cap_val,
            max_volume_cubic_ft=1000,
            storage_type=storage_type
        )

        # Refresh all routes (scenarios) that use this vehicle to update snapshots (depreciation, mpg, etc.)
        tid = _get_tenant_id() # Needed for scenario_management
        scenarios = read.view_scenarios_scoped()
        for s in scenarios:
            if s.get('vehicle_id') == vehicle_id:
                scenario_management.refresh_scenario(tid, s.get('scenario_id'))

        return True, None
    except Exception as e:
        return False, str(e)

def delete_vehicle(vehicle_id: int):
    try:
        delete.delete_vehicle_scoped(vehicle_id=vehicle_id)
        return True, None
    except Exception as e:
        if "foreign key constraint fails" in str(e).lower():
            return False, "Cannot delete vehicle: It is assigned to one or more routes."
        return False, str(e)

# --- Routes ---

def list_routes():
    scenarios = read.view_scenarios_scoped()
    if not scenarios:
        return []
    
    # Enrich with route definition names
    all_routes = read.view_routes_scoped()
    routes_map = {r['route_id']: r for r in all_routes}
    
    out = []
    for s in scenarios:
        r_def = routes_map.get(s.get('route_id'))
        
        # Map DB columns to Frontend keys
        item = {
            "route_id": s.get('scenario_id'), 
            "run_date": s.get('run_date'),
            "name": r_def.get('name') if r_def else "Unknown Route",
            "origin_location_id": r_def.get('origin_location_id') if r_def else None,
            "dest_location_id": r_def.get('dest_location_id') if r_def else None,
            "sales_amount": float(s.get('snapshot_total_revenue') or 0),
            "entered_revenue": float(s.get('snapshot_total_revenue') or 0),
            "vehicle_id": s.get('vehicle_id'),
            "driver_id": s.get('driver_id'),
            "driver_cost": float(s.get('snapshot_driver_wage') or 0),
            "load_cost": float(s.get('snapshot_driver_load_wage') or 0),
            "unload_cost": float(s.get('snapshot_driver_load_wage') or 0),
            "fuel_cost": 0.0, # Not directly in view_scenarios, calculated in details
            "depreciation_cost": 0.0,
            "insurance_cost": float(s.get('snapshot_daily_insurance') or 0),
            "gas_price": float(s.get('snapshot_gas_price') or 0),
        }
        out.append(item)
    return out

def get_route(route_id: int):
    # route_id is scenario_id
    tid = _get_tenant_id()
    details = scenario_management.get_trip_details(tid, route_id)
    if not details:
        return None
    
    header = details['header']
    
    # Need origin/dest IDs from route definition
    raw_scenarios = read.view_scenarios_scoped(ids=route_id)
    if not raw_scenarios:
        return None
    raw_s = raw_scenarios[0]
    real_route_id = raw_s.get('route_id')
    
    raw_routes = read.view_routes_scoped(ids=real_route_id)
    raw_r = raw_routes[0] if raw_routes else {}
    
    start_location = read.view_locations_scoped(ids=raw_r.get('origin_location_id'))[0]
    dest_location = read.view_locations_scoped(ids=raw_r.get('dest_location_id'))[0]
    start_address = f"{start_location.get('address_street')} {start_location.get('city')} {start_location.get('state')}"
    dest_address = f"{dest_location.get('address_street')} {dest_location.get('city')} {dest_location.get('state')}" 

    # Calculate costs
    costs = scenario_management.build_trip_costs_row(details)

    return {
        "route_id": route_id,
        "name": header.get('route_name'),
        "origin_location_id": raw_r.get('origin_location_id'),
        "dest_location_id": raw_r.get('dest_location_id'),
        "origin_address": start_address, 
        "dest_address": dest_address,
        "base_sales_amount": float(header.get('entered_revenue') or 0),
        "sales_amount": float(header.get('entered_revenue') or 0),
        "vehicle_id": raw_s.get('vehicle_id'),
        "driver_id": raw_s.get('driver_id'),
        "driver_name": header.get('driver_name'),
        "driver_cost": float(header.get('driver_drive_rate') or 0),
        "load_cost": float(header.get('driver_load_rate') or 0),
        "unload_cost": float(header.get('driver_load_rate') or 0),
        "fuel_cost": float(details.get('totals', {}).get('fuel_cost_est') or 0),
        "depreciation_cost": 0.0,
        "insurance_cost": float(header.get('daily_insurance') or 0),
        "gas_price": float(header.get('gas_price') or 0),
        # Calculated Metrics
        "calc_driver_cost": float(costs.get('driver_cost_total_est') or 0),
        "calc_fuel_cost": float(costs.get('fuel_cost_est') or 0),
        "calc_vehicle_cost": float(costs.get('depreciation_cost_est') or 0) + float(costs.get('daily_insurance') or 0) + float(costs.get('daily_maintenance_cost') or 0),
        "calc_cogs": float(costs.get('total_cogs') or 0),
        "calc_total_cost": float(costs.get('driver_cost_total_est') or 0) + float(costs.get('fuel_cost_est') or 0) + float(costs.get('depreciation_cost_est') or 0) + float(costs.get('daily_insurance') or 0) + float(costs.get('daily_maintenance_cost') or 0) + float(costs.get('total_cogs') or 0),
        
        # Audit Metrics
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
    try:
        # 1. Create Route Definition
        real_route_id = create.add_route_scoped(
            name=name,
            origin_location_id=origin_location_id,
            dest_location_id=dest_location_id
        )
        
        # 2. Create Scenario
        scenario_id = scenario_management.create_scenario(
            tenant_id=tid,
            route_id=real_route_id,
            total_revenue=sales_amount,
            vehicle_id=vehicle_id,
            driver_id=driver_id,
            current_gas_price=gas_price if gas_price is not None else 4.50
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
    try:
        # Update Scenario
        scenario_management.update_scenario(
            tenant_id=tid,
            scenario_id=route_id,
            total_revenue=sales_amount,
            vehicle_id=vehicle_id,
            driver_id=driver_id
        )
        
        # Update Route Definition
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

def delete_route(route_id: int):
    tid = _get_tenant_id()
    try:
        # route_id here refers to the scenario_id
        delete.delete_plan_scoped(scenario_id=route_id)
        return True, None
    except Exception as e:
        # Manifest items usually cascade, but if there are other constraints:
        return False, str(e)

def assign_vehicle_to_route(route_id: int, vehicle_id: Optional[int]):
    tid = _get_tenant_id()
    try:
        scenario_management.update_scenario(
            tenant_id=tid,
            scenario_id=route_id,
            vehicle_id=vehicle_id
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

def recalculate_route_costs(route_id: int):
    tid = _get_tenant_id()
    try:
        scenario_management.refresh_scenario(tid, route_id)
        return True, None
    except Exception as e:
        return False, str(e)

def get_all_routes_raw():
    tid = _get_tenant_id()
    scenarios = read.view_scenarios_scoped()
    out = []
    for s in scenarios:
        d = scenario_management.get_trip_details(tid, s['scenario_id'])
        if d: out.append(d)
    return out

def get_route_raw(route_id):
    tid = _get_tenant_id()
    return scenario_management.get_trip_details(tid, route_id)

def export_routes_csv(details_list, output_handle):
    scenario_management.export_summary_csv(details_list, output_handle)

def export_route_detailed_csv(details, output_handle):
    scenario_management.export_trip_csv(details, output_handle)

# --- Products ---

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

def create_product(product_name: str, sku: str, storage_type: str):
    try:
        # Using sku as product_code
        new_id = create.add_product_master_scoped(
            product_code=sku,
            name=product_name,
            storage_type=storage_type if storage_type else "Dry"
        )
        return True, None, new_id
    except Exception as e:
        return False, str(e), None

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

def delete_product(product_code: str):
    try:
        delete.delete_product_master_scoped(product_code=product_code)
        return True, None
    except Exception as e:
        if "foreign key constraint fails" in str(e).lower():
            return False, "Cannot delete product: It is present on one or more route manifests."
        return False, str(e)

# --- Route Products (Manifest) ---

def get_route_manifest(route_id: int):
    all_items = read.view_manifest_items_scoped()
    
    # We need to map item_name back to product_code so app.py can look up product details
    all_products = read.view_products_master_scoped()
    name_to_code = {p['name']: p['product_code'] for p in all_products}
    
    out = []
    for i in all_items:
        if i.get('scenario_id') != route_id:
            continue
            
        item_name = i.get('item_name')
        # Map name to code if possible, else use name
        p_id = name_to_code.get(item_name, item_name)
        
        out.append({
            "manifest_item_id": i.get('manifest_item_id'),
            "product_id": p_id, 
            "product_name": item_name,
            "quantity": float(i.get('quantity_loaded') or 0),
            "unit_price": i.get('snapshot_price_per_item'),
            "items_per_unit": float(i.get('snapshot_items_per_unit') or 0),
            "cost_per_item": i.get('snapshot_cost_per_item'),
            "unit_weight": i.get('snapshot_unit_weight'),
            "unit_volume": i.get('snapshot_unit_volume')
        })
    return out

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
    
    # Check if item already exists on this route
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
    # product_id passed from app.py is now product_code (mapped in get_route_manifest)
    target_code = str(product_id)
    
    # Resolve code to name to find the manifest item
    all_products = read.view_products_master_scoped()
    target_name = None
    for p in all_products:
        if str(p['product_code']) == target_code:
            target_name = p['name']
            break
    
    if not target_name:
        target_name = target_code
    
    all_items = read.view_manifest_items_scoped()
    item_to_delete = None
    
    for item in all_items:
        if item.get('scenario_id') == route_id:
            if item.get('item_name') == target_name:
                item_to_delete = item.get('manifest_item_id')
                break
    
    if item_to_delete:
        try:
            delete.delete_manifest_item_scoped(manifest_item_id=item_to_delete)
            return True, None
        except Exception as e:
            return False, str(e)
            
    return False, "Item not found in manifest"