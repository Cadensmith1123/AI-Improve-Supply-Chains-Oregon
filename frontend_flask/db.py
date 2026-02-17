# db.py
# Mock data now. Later teammate replaces these with stored procedure calls.

_LOCATIONS = [
    {"location_id": 1, "name": "Portland Hub"},
    {"location_id": 2, "name": "Seattle DC"},
    {"location_id": 3, "name": "Salem Store"},
]

# Vehicles (simple mock table)
_VEHICLES = [
    {"vehicle_id": 1, "vehicle_name": "Truck-1", "mpg": "8.5", "fuel_price": "4.25", "capacity": "26 pallets"},
    {"vehicle_id": 2, "vehicle_name": "Van-1", "mpg": "14", "fuel_price": "4.25", "capacity": "10 pallets"},
]

# Routes now include vehicle_id and cost placeholders
_ROUTES = [
    {
        "route_id": 101,
        "name": "PDX → SEA",
        "origin_location_id": 1,
        "dest_location_id": 2,
        "origin_address": "123 SW Main St, Portland, OR 97201",
        "dest_address": "800 Pike St, Seattle, WA 98101",
        "base_sales_amount": 1200.50,
        "sales_amount": 1200.50,
        "vehicle_id": 1,
        "driver_cost": None,
        "load_cost": None,
        "unload_cost": None,
        "fuel_cost": None,
        "depreciation_cost": None,
        "insurance_cost": None,
    },
    {
        "route_id": 102,
        "name": "SEA → SLM",
        "origin_location_id": 2,
        "dest_location_id": 3,
        "origin_address": "800 Pike St, Seattle, WA 98101",
        "dest_address": "200 State St, Salem, OR 97301",
        "base_sales_amount": 950.00,
        "sales_amount": 950.00,
        "vehicle_id": None,
        "driver_cost": 120.0,
        "load_cost": 25.0,
        "unload_cost": 25.0,
        "fuel_cost": 80.0,
        "depreciation_cost": 15.0,
        "insurance_cost": 10.0,
    },
]

# Products (global catalog) — NO quantity here (quantities are per-route)
_PRODUCTS = [
    {
        "product_id": 1,
        "product_name": "Apples",
        "sku": "APL-001",
        "category": "Produce",
        "unit": "cases",
        "unit_price": 28.50,
    },
    {
        "product_id": 2,
        "product_name": "Oranges",
        "sku": "ORG-002",
        "category": "Produce",
        "unit": "cases",
        "unit_price": 31.25,
    },
]

# Join table: products carried on routes (route-specific quantities)
_ROUTE_PRODUCTS = [
    {"route_id": 101, "product_id": 1, "quantity": 20},
    {"route_id": 101, "product_id": 2, "quantity": 10},
    {"route_id": 102, "product_id": 1, "quantity": 6},
]


# --------------------
# Helpers
# --------------------

def _recalc_route_sales_amount(route_id: int) -> None:
    """
    sales_amount = base_sales_amount + sum(unit_price * quantity) for manifest lines.
    unit_price None => 0.0
    """
    route = get_route(route_id)
    if not route:
        return

    base = route.get("base_sales_amount")
    try:
        base_f = float(base) if base is not None else 0.0
    except (TypeError, ValueError):
        base_f = 0.0

    total = 0.0
    for rp in _ROUTE_PRODUCTS:
        if rp["route_id"] != route_id:
            continue
        p = get_product(rp["product_id"])
        if not p:
            continue

        unit_price = p.get("unit_price")
        qty = rp.get("quantity", 0)

        try:
            unit_price_f = float(unit_price) if unit_price is not None else 0.0
        except (TypeError, ValueError):
            unit_price_f = 0.0

        try:
            qty_i = int(qty)
        except (TypeError, ValueError):
            qty_i = 0

        total += unit_price_f * qty_i

    route["sales_amount"] = float(base_f + total)


# --------------------
# Locations
# --------------------

def list_locations():
    return _LOCATIONS


def create_location(name: str, region: str):
    new_id = max([l["location_id"] for l in _LOCATIONS], default=0) + 1
    display_name = name if not region else f"{name} ({region})"
    _LOCATIONS.append({"location_id": new_id, "name": display_name})
    return True, None, new_id


# --------------------
# Vehicles
# --------------------

def list_vehicles():
    return _VEHICLES


def get_vehicle(vehicle_id: int):
    for v in _VEHICLES:
        if v["vehicle_id"] == vehicle_id:
            return v
    return None


def create_vehicle(vehicle_name: str, mpg: str, fuel_price: str, capacity: str):
    if not vehicle_name:
        return False, "REQUIRED", None

    new_id = max([v["vehicle_id"] for v in _VEHICLES], default=0) + 1
    _VEHICLES.append({
        "vehicle_id": new_id,
        "vehicle_name": vehicle_name,
        "mpg": mpg,
        "fuel_price": fuel_price,
        "capacity": capacity,
    })
    return True, None, new_id


# --------------------
# Routes
# --------------------

def list_routes():
    return _ROUTES


def get_route(route_id: int):
    for r in _ROUTES:
        if r["route_id"] == route_id:
            return r
    return None


def create_route(
    name: str,
    origin_location_id: int,
    dest_location_id: int,
    origin_address: str,
    dest_address: str,
    sales_amount: float,
    vehicle_id: int | None,
    driver_cost: float | None,
    load_cost: float | None,
    unload_cost: float | None,
    fuel_cost: float | None,
    depreciation_cost: float | None,
    insurance_cost: float | None,
):
    loc_ids = {l["location_id"] for l in _LOCATIONS}
    if origin_location_id not in loc_ids or dest_location_id not in loc_ids:
        return False, "FK_ERROR", None

    if vehicle_id is not None and not get_vehicle(vehicle_id):
        return False, "FK_ERROR", None

    new_id = max([r["route_id"] for r in _ROUTES], default=100) + 1
    _ROUTES.append({
        "route_id": new_id,
        "name": name,
        "origin_location_id": origin_location_id,
        "dest_location_id": dest_location_id,
        "origin_address": origin_address,
        "dest_address": dest_address,
        "base_sales_amount": sales_amount,
        "sales_amount": sales_amount,
        "vehicle_id": vehicle_id,
        "driver_cost": driver_cost,
        "load_cost": load_cost,
        "unload_cost": unload_cost,
        "fuel_cost": fuel_cost,
        "depreciation_cost": depreciation_cost,
        "insurance_cost": insurance_cost,
    })

    _recalc_route_sales_amount(new_id)
    return True, None, new_id


def update_route(
    route_id: int,
    name: str,
    origin_location_id: int,
    dest_location_id: int,
    origin_address: str,
    dest_address: str,
    sales_amount: float,
    driver_cost: float | None,
    load_cost: float | None,
    unload_cost: float | None,
    fuel_cost: float | None,
    depreciation_cost: float | None,
    insurance_cost: float | None,
    vehicle_id: int | None = None,
):
    route = get_route(route_id)
    if not route:
        return False, "NOT_FOUND"

    loc_ids = {l["location_id"] for l in _LOCATIONS}
    if origin_location_id not in loc_ids or dest_location_id not in loc_ids:
        return False, "FK_ERROR"

    if vehicle_id is not None and not get_vehicle(vehicle_id):
        return False, "FK_ERROR"

    route["name"] = name
    route["origin_location_id"] = origin_location_id
    route["dest_location_id"] = dest_location_id
    route["origin_address"] = origin_address
    route["dest_address"] = dest_address

    route["base_sales_amount"] = sales_amount
    route["sales_amount"] = sales_amount

    route["driver_cost"] = driver_cost
    route["load_cost"] = load_cost
    route["unload_cost"] = unload_cost
    route["fuel_cost"] = fuel_cost
    route["depreciation_cost"] = depreciation_cost
    route["insurance_cost"] = insurance_cost

    if vehicle_id is not None:
        route["vehicle_id"] = vehicle_id

    _recalc_route_sales_amount(route_id)
    return True, None


def assign_vehicle_to_route(route_id: int, vehicle_id: int | None):
    route = get_route(route_id)
    if not route:
        return False, "NOT_FOUND"

    if vehicle_id is not None and not get_vehicle(vehicle_id):
        return False, "FK_ERROR"

    route["vehicle_id"] = vehicle_id
    return True, None


# --------------------
# Products
# --------------------

def list_products():
    return _PRODUCTS


def get_product(product_id: int):
    for p in _PRODUCTS:
        if p["product_id"] == product_id:
            return p
    return None


def create_product(product_name: str, sku: str, category: str, unit: str, unit_price: float | None):
    new_id = max([p["product_id"] for p in _PRODUCTS], default=0) + 1
    _PRODUCTS.append({
        "product_id": new_id,
        "product_name": product_name,
        "sku": sku,
        "category": category,
        "unit": unit,
        "unit_price": unit_price,
    })
    return True, None, new_id


def update_product(product_id: int, product_name: str, sku: str, category: str, unit: str, unit_price: float | None):
    p = get_product(product_id)
    if not p:
        return False, "NOT_FOUND"

    p["product_name"] = product_name
    p["sku"] = sku
    p["category"] = category
    p["unit"] = unit
    p["unit_price"] = unit_price
    return True, None


# --------------------
# Route Products (Manifest)
# --------------------

def get_route_manifest(route_id: int):
    out = []
    for rp in _ROUTE_PRODUCTS:
        if rp["route_id"] != route_id:
            continue
        p = get_product(rp["product_id"])
        if not p:
            continue
        out.append({
            "product_id": rp["product_id"],
            "product_name": p["product_name"],
            "quantity": rp["quantity"],
        })
    out.sort(key=lambda x: x["product_name"].lower())
    return out


def add_product_to_route(route_id: int, product_id: int, quantity: int):
    if not get_route(route_id):
        return False, "ROUTE_NOT_FOUND"
    if not get_product(product_id):
        return False, "PRODUCT_NOT_FOUND"
    if quantity <= 0:
        return False, "BAD_QTY"

    for rp in _ROUTE_PRODUCTS:
        if rp["route_id"] == route_id and rp["product_id"] == product_id:
            # CHANGED: add to existing quantity instead of replacing it
            rp["quantity"] = int(rp.get("quantity", 0)) + int(quantity)
            _recalc_route_sales_amount(route_id)
            return True, None

    _ROUTE_PRODUCTS.append({"route_id": route_id, "product_id": product_id, "quantity": quantity})
    _recalc_route_sales_amount(route_id)
    return True, None


def remove_product_from_route(route_id: int, product_id: int):
    before = len(_ROUTE_PRODUCTS)
    _ROUTE_PRODUCTS[:] = [
        rp for rp in _ROUTE_PRODUCTS
        if not (rp["route_id"] == route_id and rp["product_id"] == product_id)
    ]
    if len(_ROUTE_PRODUCTS) == before:
        return False, "NOT_FOUND"

    _recalc_route_sales_amount(route_id)
    return True, None


# Normalize existing sample routes on import to match manifests
for _r in _ROUTES:
    if "base_sales_amount" not in _r:
        _r["base_sales_amount"] = _r.get("sales_amount", 0.0)
    _recalc_route_sales_amount(_r["route_id"])
