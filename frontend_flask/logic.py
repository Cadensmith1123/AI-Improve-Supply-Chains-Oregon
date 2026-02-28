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
        errors["quantity"] = "Quantity is required."
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


def calculate_route_cost(route):
    total_cost = 0.0
    for k in ["driver_cost", "load_cost", "unload_cost", "fuel_cost", "depreciation_cost", "insurance_cost"]:
        v = route.get(k)
        total_cost += float(v) if v is not None else 0.0
    return total_cost


def calculate_manifest_item_metrics(item, product=None):
    unit_price = item.get("unit_price")
    if unit_price is None and product:
        unit_price = product.get("unit_price")
    
    try:
        unit_price_f = float(unit_price) if unit_price is not None else 0.0
    except (TypeError, ValueError):
        unit_price_f = 0.0

    try:
        qty = float(item.get("quantity", 0))
    except (TypeError, ValueError):
        qty = 0

    try:
        items_per_unit = float(item.get("items_per_unit") or 1)
    except (TypeError, ValueError):
        items_per_unit = 1.0

    line_total = unit_price_f * qty * items_per_unit
    
    return {
        "quantity": qty,
        "unit_price": unit_price_f,
        "items_per_unit": items_per_unit,
        "line_total": line_total
    }