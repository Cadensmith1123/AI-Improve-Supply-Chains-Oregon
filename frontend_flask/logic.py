from decimal import Decimal
import pandas as pd
import depreciation_insurance

def parse_optional_float(raw: str, field_key: str, errors: dict):
    raw = (raw or "").strip()
    if raw == "":
        return None
    try:
        return float(raw)
    except ValueError:
        errors[field_key] = "Must be numeric."
        return None


def parse_optional_int(raw: str, field_key: str, errors: dict):
    raw = (raw or "").strip()
    if raw == "":
        return None
    try:
        return int(raw)
    except ValueError:
        errors[field_key] = "Must be a whole number."
        return None


def validate_route_form(form):
    errors = {}

    name = (form.get("name") or "").strip()
    origin_raw = (form.get("origin_location_id") or "").strip()
    dest_raw = (form.get("dest_location_id") or "").strip()

    sales_raw = (form.get("sales_amount") or "").strip()

    vehicle_raw = (form.get("vehicle_id") or "").strip()
    driver_raw = (form.get("driver_id") or "").strip()
    gas_raw = (form.get("gas_price") or "").strip()

    if not origin_raw:
        errors["origin_location_id"] = "Start is required."
    if not dest_raw:
        errors["dest_location_id"] = "Destination is required."
    if not sales_raw:
        errors["sales_amount"] = "Sales amount is required."

    origin_id = None
    dest_id = None
    sales_amount = None
    vehicle_id = None
    driver_id = None

    if origin_raw:
        try:
            origin_id = int(origin_raw)
        except ValueError:
            errors["origin_location_id"] = "Start must be a valid location."

    if dest_raw:
        try:
            dest_id = int(dest_raw)
        except ValueError:
            errors["dest_location_id"] = "Destination must be a valid location."

    if origin_id is not None and dest_id is not None and origin_id == dest_id:
        errors["dest_location_id"] = "Destination must be different from start."

    if sales_raw:
        try:
            sales_amount = float(sales_raw)
        except ValueError:
            errors["sales_amount"] = "Sales amount must be numeric (e.g., 1200.50)."

    if vehicle_raw:
        try:
            vehicle_id = int(vehicle_raw)
        except ValueError:
            errors["vehicle_id"] = "Vehicle must be valid."

    if driver_raw:
        try:
            driver_id = int(driver_raw)
        except ValueError:
            errors["driver_id"] = "Driver must be valid."

    gas_price = parse_optional_float(gas_raw, "gas_price", errors)
    driver_cost = parse_optional_float(form.get("driver_cost"), "driver_cost", errors)
    load_cost = parse_optional_float(form.get("load_cost"), "load_cost", errors)
    unload_cost = parse_optional_float(form.get("unload_cost"), "unload_cost", errors)
    fuel_cost = parse_optional_float(form.get("fuel_cost"), "fuel_cost", errors)
    depreciation_cost = parse_optional_float(form.get("depreciation_cost"), "depreciation_cost", errors)
    insurance_cost = parse_optional_float(form.get("insurance_cost"), "insurance_cost", errors)

    data = {
        "name": name,
        "origin_location_id": origin_id,
        "dest_location_id": dest_id,
        "origin_address": "",
        "dest_address": "",
        "sales_amount": sales_amount,
        "vehicle_id": vehicle_id,
        "driver_id": driver_id,
        "gas_price": gas_price,
        "driver_cost": driver_cost,
        "load_cost": load_cost,
        "unload_cost": unload_cost,
        "fuel_cost": fuel_cost,
        "depreciation_cost": depreciation_cost,
        "insurance_cost": insurance_cost,
    }
    return data, errors


def validate_product_form(form):
    errors = {}
    product_name = (form.get("product_name") or "").strip()
    sku = (form.get("sku") or "").strip()
    storage_type = (form.get("storage_type") or "").strip()

    if not product_name:
        errors["product_name"] = "Product name is required."
    if not sku:
        errors["sku"] = "SKU is required."

    data = {
        "product_name": product_name,
        "sku": sku,
        "storage_type": storage_type,
    }
    return data, errors


def validate_load_form(form):
    errors = {}
    product_raw = (form.get("product_id") or "").strip()
    qty_raw = (form.get("quantity") or "").strip()
    price_raw = (form.get("price_per_item") or "").strip()
    items_per_unit_raw = (form.get("items_per_unit") or "").strip()
    cost_raw = (form.get("cost_per_item") or "").strip()
    weight_raw = (form.get("unit_weight") or "").strip()
    volume_raw = (form.get("unit_volume") or "").strip()

    product_id = None
    quantity = None

    if not product_raw:
        errors["product_id"] = "Product is required."
    else:
        product_id = product_raw

    if not qty_raw:
        quantity = 1.0
    else:
        try:
            quantity = float(qty_raw)
            if quantity <= 0:
                errors["quantity"] = "Quantity must be greater than 0."
        except ValueError:
            errors["quantity"] = "Quantity must be a number."

    data = {
        "product_id": product_id,
        "quantity": quantity,
        "price_per_item": parse_optional_float(price_raw, "price_per_item", errors),
        "items_per_unit": parse_optional_float(items_per_unit_raw, "items_per_unit", errors),
        "cost_per_item": parse_optional_float(cost_raw, "cost_per_item", errors),
        "unit_weight": parse_optional_float(weight_raw, "unit_weight", errors),
        "unit_volume": parse_optional_float(volume_raw, "unit_volume", errors),
    }
    return data, errors


def safe_float(val, default=0.0):
    """Safely converts a value to float, returning default on failure."""
    if val is None:
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


def safe_int(val, default=0):
    """Safely converts a value to int, returning default on failure."""
    if val is None:
        return default
    try:
        # Handle strings like "30.0" by converting to float first
        return int(float(val))
    except (ValueError, TypeError):
        return default


def to_decimal(val, default="0"):
    """Helper to safely convert values to Decimal."""
    if val is None:
        return Decimal(default)
    try:
        return Decimal(str(val))
    except Exception:
        return Decimal(default)

def parse_capacity_string(capacity, default=1000.0):
    """Parses a capacity string like '1000 lbs' into a float."""
    cap_str = str(capacity).split()[0] if capacity else ""
    return safe_float(cap_str, default)

def get_trip_length():
    """
    Returns trip distance (miles) and time (minutes).
    Currently a stub for a future external API call.
    """
    miles_est =  25.2
    time_est = 80.5
    return miles_est, time_est

def calculate_depreciation(purchase_price, salvage_value, yearly_mileage, trip_miles):
    depreciation_cost = depreciation_insurance.trip_depreciation_cost(
        purchase_price, salvage_value, yearly_mileage, trip_miles
    )
    return depreciation_cost

def calculate_insurance(annual_insurance_cost, yearly_mileage, trip_miles):
    insurance_cost = depreciation_insurance.trip_insurance_cost(annual_insurance_cost, yearly_mileage, trip_miles)
    return insurance_cost


def calculate_maintenance(annual_maintenance_cost, yearly_mileage, trip_miles):
    # Maintenance is calculated same as insurance (Annual / Yearly Miles * Trip Miles)
    return depreciation_insurance.trip_insurance_cost(annual_maintenance_cost, yearly_mileage, trip_miles)

def calculate_operating_costs(vehicle, trip_miles):
    """
    Calculates operating costs (depreciation, insurance, maintenance) for a vehicle.
    Returns tuple: (depreciation_per_mile, daily_insurance, daily_maintenance)
    """
    if not vehicle:
        return Decimal("0.0"), Decimal("0.0"), Decimal("0.0")
    
    # Extract values safely
    purchase_price = vehicle.get('vehicle_purchase_price')
    salvage_value = vehicle.get('vehicle_estimated_salvage_value')
    yearly_mileage = vehicle.get('vehicle_estimated_yearly_milage')
    annual_insurance = vehicle.get('annual_insurance_cost')
    annual_maintenance = vehicle.get('annual_maintenance_cost')

    dep = calculate_depreciation(purchase_price, salvage_value, yearly_mileage, trip_miles)
    ins = calculate_insurance(annual_insurance, yearly_mileage, trip_miles)
    maint = calculate_maintenance(annual_maintenance, yearly_mileage, trip_miles)
    
    return dep, ins, maint

def calculate_driver_costs(drive_minutes, load_minutes, unload_minutes, drive_rate, load_rate):
    """
    Calculates driver costs based on time and rates.
    Returns tuple: (drive_cost, load_cost, unload_cost, total_driver_cost)
    """
    drive_cost = (drive_minutes / 60) * drive_rate
    load_cost = (load_minutes / 60) * load_rate
    unload_cost = (unload_minutes / 60) * load_rate
    total_cost = drive_cost + load_cost + unload_cost
    
    return drive_cost, load_cost, unload_cost, total_cost

def calculate_fuel_cost(miles, mpg, gas_price, estimated_cost=0.0):
    """
    Calculates fuel cost based on mileage, MPG, and gas price.
    Prioritizes estimated_cost if provided (e.g. from external API).
    """
    if estimated_cost > 0:
        return estimated_cost
        
    if mpg > 0:
        return (miles / mpg) * gas_price
        
    return 0.0


def calculate_trip_costs(header, items, totals=None):
    """
    Calculates the full financial breakdown of a trip.
    """
    if totals is None:
        totals = {}

    drive_rate = safe_float(header.get("driver_drive_rate"))
    load_rate = safe_float(header.get("driver_load_rate"))
    daily_ins = safe_float(header.get("daily_insurance"))
    depreciation_cost = safe_float(header.get("depreciation_per_mile"))
    maintenance_cost = safe_float(header.get("daily_maintenance_cost"))
    
    vehicle_mpg = safe_float(header.get("vehicle_mpg"))
    gas_price = safe_float(header.get("gas_price"))

    load_min = safe_float(header.get("plan_load_min"))
    unload_min = safe_float(header.get("plan_unload_min"))
    miles_est, drive_min = get_trip_length()

    driver_drive_cost, driver_load_cost, driver_unload_cost, driver_total_cost = calculate_driver_costs(
        drive_min, load_min, unload_min, drive_rate, load_rate
    )

    est_fuel = safe_float(totals.get("fuel_cost_est"))
    final_fuel_cost = calculate_fuel_cost(miles_est, vehicle_mpg, gas_price, est_fuel)

    total_cogs = safe_float(totals.get("total_cogs"))
    total_weight = safe_float(totals.get("total_weight_lbs"))
    total_volume = safe_float(totals.get("total_volume"))
    calculated_revenue = safe_float(totals.get("calculated_revenue"))
    entered_revenue = safe_float(header.get("entered_revenue"))

    total_cost_est = total_cogs + driver_total_cost + daily_ins + maintenance_cost + final_fuel_cost + depreciation_cost

    profit_vs_entered = entered_revenue - total_cost_est
    profit_vs_calculated = calculated_revenue - total_cost_est

    return {
        "scenario_id": header.get("scenario_id"),
        "run_date": header.get("run_date"),
        "route_name": header.get("route_name"),
        "origin_name": header.get("origin_name"),
        "dest_name": header.get("dest_name"),
        "vehicle_name": header.get("vehicle_name"),
        "driver_name": header.get("driver_name"),

        "drive_minutes_est": drive_min,
        "load_minutes_plan": load_min,
        "unload_minutes_plan": unload_min,

        "driver_drive_rate_per_hr": drive_rate,
        "driver_load_rate_per_hr": load_rate,
        "gas_price": gas_price,

        "daily_insurance": daily_ins,
        "daily_maintenance_cost": maintenance_cost,
        "depreciation_cost_est": round(depreciation_cost, 2),
        "fuel_cost_est": round(final_fuel_cost, 2),

        "driver_drive_cost_est": round(driver_drive_cost, 2),
        "driver_load_cost_est": round(driver_load_cost, 2),
        "driver_unload_cost_est": round(driver_unload_cost, 2),
        "driver_cost_total_est": round(driver_total_cost, 2),

        "line_item_count": len(items),
        "total_weight_lbs": round(total_weight, 2),
        "total_volume": round(total_volume, 2),

        "total_cogs": round(total_cogs, 2),
        "entered_revenue": round(entered_revenue, 2),
        "calculated_revenue": round(calculated_revenue, 2),

        "profit_est_entered": round(profit_vs_entered, 2),
        "profit_est_calculated": round(profit_vs_calculated, 2),

        "margin_est_entered": round((profit_vs_entered / entered_revenue) if entered_revenue else 0, 4),
        "margin_est_calculated": round((profit_vs_calculated / calculated_revenue) if calculated_revenue else 0, 4),
        "total_distance_miles": round(miles_est, 1),
        
        "total_cost": round(total_cost_est, 2)
    }


def calculate_manifest_item_metrics(item, product=None):
    """
    Calculates metrics for a single line item.
    Used by both the UI (preview) and the Backend (aggregation).
    """
    unit_price = item.get("unit_price")
    if unit_price is None or unit_price == "":
        unit_price = item.get("price_per_item")

    if (unit_price is None or unit_price == "") and product:
        unit_price = product.get("unit_price")
    
    unit_price_f = safe_float(unit_price)
    
    qty_val = item.get("quantity")
    if qty_val is None or qty_val == "":
        qty_val = item.get("quantity_loaded")
    qty = safe_float(qty_val)
    
    items_per_unit = safe_float(item.get("items_per_unit"), 1.0)

    cost = safe_float(item.get("cost_per_item"))
    weight = safe_float(item.get("unit_weight") or item.get("unit_weight_lbs"))
    volume = safe_float(item.get("unit_volume"))

    line_total = round(unit_price_f * qty * items_per_unit, 2)
    line_cogs = round(cost * qty * items_per_unit, 2)
    line_weight = round(weight * qty, 2)
    line_volume = round(volume * qty, 2)
    
    return {
        "quantity": qty,
        "unit_price": unit_price_f,
        "items_per_unit": items_per_unit,
        "line_total": line_total,
        
        "line_cogs": line_cogs,
        "line_weight": line_weight,
        "line_volume": line_volume
    }


def aggregate_manifest_totals(items):
    """
    Calculates aggregate totals (COGS, revenue, weight, volume) for a list of manifest items.
    """
    total_cogs = 0.0
    total_rev = 0.0
    total_weight = 0.0
    total_volume = 0.0
    
    for i in items:
        m = calculate_manifest_item_metrics(i)
        total_cogs += m["line_cogs"]
        total_rev += m["line_total"]
        total_weight += m["line_weight"]
        total_volume += m["line_volume"]
        
    return {
        "total_cogs": round(total_cogs, 2),
        "calculated_revenue": round(total_rev, 2),
        "total_weight_lbs": round(total_weight, 2),
        "total_volume": round(total_volume, 2)
    }


def generate_csv_export(data_list, columns=None):
    """
    Generates CSV string from list of dicts.
    columns: Optional list of column names to include and order.
    """
    if not data_list:
        return ""
    
    df = pd.DataFrame(data_list)
    if columns:
        # Filter and order columns, ignoring those that don't exist in the data
        valid_cols = [c for c in columns if c in df.columns]
        if valid_cols:
            df = df[valid_cols]
            
    return df.to_csv(index=False)