# access_db.py
from flask import g
from typing import Optional
from db.functions.simple_functions import read, create, update, delete
from db.functions import scenario_management
from decimal import Decimal

# Helper to get tenant_id safely
def _get_tenant_id():
    try:
        return g.tenant_id
    except (RuntimeError, AttributeError):
        return 1

# --------------------
# Locations
# --------------------

def list_locations():
    tid = _get_tenant_id()
    return read.view_locations(tid)

def create_location(name: str, region: str):
    tid = _get_tenant_id()
    try:
        new_id = create.add_location(
            tenant_id=tid,
            name=name,
            type="Hub",
            address_street="Unknown",
            city=region if region else "Unknown",
            state="OR",
            zip_code="00000",
            phone="000-000-0000",
            latitude=0.0,
            longitude=0.0,
            avg_load_minutes=30,
            avg_unload_minutes=30
        )
        return True, None, new_id
    except Exception as e:
        return False, str(e), None

# --------------------
# Vehicles
# --------------------

def list_vehicles():
    tid = _get_tenant_id()
    rows = read.view_vehicles(tid)
    for r in rows:
        r['vehicle_name'] = r.get('name')
    return rows

def get_vehicle(vehicle_id: int):
    tid = _get_tenant_id()
    rows = read.view_vehicles(tid, ids=vehicle_id)
    if rows:
        rows[0]['vehicle_name'] = rows[0].get('name')
        return rows[0]
    return None

def create_vehicle(vehicle_name: str, mpg: str, fuel_price: str, capacity: str):
    tid = _get_tenant_id()
    try:
        # capacity -> max_weight_lbs parsing
        cap_val = 1000
        if capacity:
            try:
                cap_val = float(capacity.split()[0])
            except:
                pass
        
        new_id = create.add_vehicle(
            tenant_id=tid,
            name=vehicle_name,
            mpg=float(mpg) if mpg else 10.0,
            depreciation_per_mile=0.0,
            annual_insurance_cost=0.0,
            annual_maintenance_cost=0.0,
            max_weight_lbs=cap_val,
            max_volume_cubic_ft=1000,
            storage_type="Dry"
        )
        return True, None, new_id
    except Exception as e:
        return False, str(e), None

# --------------------
# Routes
# --------------------

def list_routes():
    tid = _get_tenant_id()
    scenarios = read.view_scenarios(tid)
    if not scenarios:
        return []
    
    # Enrich with route definition names
    all_routes = read.view_routes(tid)
    routes_map = {r['route_id']: r for r in all_routes}
    
    out = []
    for s in scenarios:
        r_def = routes_map.get(s.get('route_id'))
        
        # Map DB columns to Frontend keys
        item = {
            "route_id": s.get('scenario_id'), 
            "name": r_def.get('name') if r_def else "Unknown Route",
            "origin_location_id": r_def.get('origin_location_id') if r_def else None,
            "dest_location_id": r_def.get('dest_location_id') if r_def else None,
            "sales_amount": float(s.get('entered_revenue') or 0),
            "vehicle_id": s.get('vehicle_id'),
            "driver_cost": float(s.get('snapshot_driver_wage') or 0),
            "load_cost": float(s.get('snapshot_driver_load_wage') or 0),
            "unload_cost": float(s.get('snapshot_driver_load_wage') or 0),
            "fuel_cost": 0.0, # Not directly in view_scenarios, calculated in details
            "depreciation_cost": 0.0,
            "insurance_cost": float(s.get('snapshot_daily_insurance') or 0),
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
    raw_scenarios = read.view_scenarios(tid, ids=route_id)
    if not raw_scenarios:
        return None
    raw_s = raw_scenarios[0]
    real_route_id = raw_s.get('route_id')
    
    raw_routes = read.view_routes(tid, ids=real_route_id)
    raw_r = raw_routes[0] if raw_routes else {}
    
    start_location = read.view_locations(tid, ids=raw_r.get('origin_location_id'))[0]
    dest_location = read.view_locations(tid, ids=raw_r.get('dest_location_id'))[0]
    start_address = f"{start_location.get('address_street')} {start_location.get('city')} {start_location.get('state')}"
    dest_address = f"{dest_location.get('address_street')} {dest_location.get('city')} {dest_location.get('state')}" 

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
        "driver_cost": float(header.get('driver_drive_rate') or 0),
        "load_cost": float(header.get('driver_load_rate') or 0),
        "unload_cost": float(header.get('driver_load_rate') or 0),
        "fuel_cost": float(details.get('totals', {}).get('fuel_cost_est') or 0),
        "depreciation_cost": 0.0,
        "insurance_cost": float(header.get('daily_insurance') or 0),
    }

def create_route(
    name: str,
    origin_location_id: int,
    dest_location_id: int,
    origin_address: str,
    dest_address: str,
    sales_amount: float,
    vehicle_id: Optional[int],
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
        real_route_id = create.add_route(
            tenant_id=tid,
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
            driver_id=None,
            current_gas_price=4.50
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
):
    tid = _get_tenant_id()
    try:
        # Update Scenario
        scenario_management.update_scenario(
            tenant_id=tid,
            scenario_id=route_id,
            total_revenue=sales_amount,
            vehicle_id=vehicle_id
        )
        
        # Update Route Definition
        raw_scenarios = read.view_scenarios(tid, ids=route_id)
        if raw_scenarios:
            real_route_id = raw_scenarios[0].get('route_id')
            update.update_route(
                tenant_id=tid,
                route_id=real_route_id,
                name=name,
                origin_location_id=origin_location_id,
                dest_location_id=dest_location_id
            )
            
        return True, None
    except Exception as e:
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

# --------------------
# Products
# --------------------

def list_products():
    tid = _get_tenant_id()
    rows = read.view_products_master(tid)
    for r in rows:
        r['product_name'] = r.get('name')
        r['product_id'] = r.get('product_code')
    return rows

def get_product(product_id):
    tid = _get_tenant_id()
    rows = read.view_products_master(tid, ids=product_id)
    if rows:
        rows[0]['product_name'] = rows[0].get('name')
        rows[0]['product_id'] = rows[0].get('product_code')
        return rows[0]
    return None

def create_product(product_name: str, sku: str, category: str, unit: str, unit_price: Optional[float]):
    tid = _get_tenant_id()
    try:
        # Using sku as product_code
        new_id = create.add_product_master(
            tenant_id=tid,
            product_code=sku,
            name=product_name,
            storage_type="Dry"
        )
        return True, None, new_id
    except Exception as e:
        return False, str(e), None

def update_product(product_id: int, product_name: str, sku: str, category: str, unit: str, unit_price: Optional[float]):
    tid = _get_tenant_id()
    try:
        update.update_product_master(
            tenant_id=tid,
            product_code=product_id,
            name=product_name,
            storage_type="Dry"
        )
        return True, None
    except Exception as e:
        return False, str(e)

# --------------------
# Route Products (Manifest)
# --------------------

def get_route_manifest(route_id: int):
    tid = _get_tenant_id()
    
    # Reverting to direct fetch as requested to match mock data structure logic
    # Fetch all items and filter (or could call get_trip_details per route)
    all_items = read.view_manifest_items(tid)
    
    # We need to map item_name back to product_code so app.py can look up product details
    all_products = read.view_products_master(tid)
    name_to_code = {p['name']: p['product_code'] for p in all_products}
    
    out = []
    for i in all_items:
        if i.get('scenario_id') != route_id:
            continue
            
        item_name = i.get('item_name')
        # Map name to code if possible, else use name
        p_id = name_to_code.get(item_name, item_name)
        
        out.append({
            "product_id": p_id, 
            "product_name": item_name,
            "quantity": i.get('quantity_loaded')
        })
    return out

def add_product_to_route(route_id: int, product_id, quantity: int):
    tid = _get_tenant_id()
    prod = get_product(product_id)
    if not prod:
        return False, "Product not found"
    
    try:
        scenario_management.add_manifest_items(
            tenant_id=tid,
            scenario_id=route_id,
            item_name=prod['name'],
            quantity_loaded=quantity,
            cost_per_item=0.0,
            price_per_item=0.0
        )
        return True, None
    except Exception as e:
        return False, str(e)

def remove_product_from_route(route_id: int, product_id):
    tid = _get_tenant_id()
    # product_id passed from app.py is now product_code (mapped in get_route_manifest)
    target_code = str(product_id)
    
    # Resolve code to name to find the manifest item
    all_products = read.view_products_master(tid)
    target_name = None
    for p in all_products:
        if str(p['product_code']) == target_code:
            target_name = p['name']
            break
    
    if not target_name:
        target_name = target_code
    
    all_items = read.view_manifest_items(tid)
    item_to_delete = None
    
    for item in all_items:
        if item.get('scenario_id') == route_id:
            if item.get('item_name') == target_name:
                item_to_delete = item.get('manifest_item_id')
                break
    
    if item_to_delete:
        try:
            delete.delete_manifest_item(tid, item_to_delete)
            return True, None
        except Exception as e:
            return False, str(e)
            
    return False, "Item not found in manifest"