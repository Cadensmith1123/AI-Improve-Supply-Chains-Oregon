# app.py
import sys
import os

# Add parent directory to path so we can import 'db' package
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Flask, render_template, request, redirect, url_for, abort
import access_db as db
# import blueprint
from map_route import map_bp

app = Flask(__name__)

# register the blueprint
app.register_blueprint(map_bp)


def _parse_optional_float(raw: str, field_key: str, errors: dict):
    raw = (raw or "").strip()
    if raw == "":
        return None
    try:
        return float(raw)
    except ValueError:
        errors[field_key] = "Must be numeric."
        return None


def _parse_optional_int(raw: str, field_key: str, errors: dict):
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

    origin_address = (form.get("origin_address") or "").strip()
    dest_address = (form.get("dest_address") or "").strip()

    sales_raw = (form.get("sales_amount") or "").strip()

    vehicle_raw = (form.get("vehicle_id") or "").strip()

    if not origin_raw:
        errors["origin_location_id"] = "Start is required."
    if not dest_raw:
        errors["dest_location_id"] = "Destination is required."
    if not origin_address:
        errors["origin_address"] = "Origin address is required."
    if not dest_address:
        errors["dest_address"] = "Destination address is required."
    if not sales_raw:
        errors["sales_amount"] = "Sales amount is required."

    origin_id = None
    dest_id = None
    sales_amount = None
    vehicle_id = None

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

    driver_cost = _parse_optional_float(form.get("driver_cost"), "driver_cost", errors)
    load_cost = _parse_optional_float(form.get("load_cost"), "load_cost", errors)
    unload_cost = _parse_optional_float(form.get("unload_cost"), "unload_cost", errors)
    fuel_cost = _parse_optional_float(form.get("fuel_cost"), "fuel_cost", errors)
    depreciation_cost = _parse_optional_float(form.get("depreciation_cost"), "depreciation_cost", errors)
    insurance_cost = _parse_optional_float(form.get("insurance_cost"), "insurance_cost", errors)

    data = {
        "name": name,
        "origin_location_id": origin_id,
        "dest_location_id": dest_id,
        "origin_address": origin_address,
        "dest_address": dest_address,
        "sales_amount": sales_amount,
        "vehicle_id": vehicle_id,
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
    category = (form.get("category") or "").strip()
    unit = (form.get("unit") or "").strip()

    if not product_name:
        errors["product_name"] = "Product name is required."

    unit_price = _parse_optional_float(form.get("unit_price"), "unit_price", errors)

    data = {
        "product_name": product_name,
        "sku": sku,
        "category": category,
        "unit": unit,
        "unit_price": unit_price,
    }
    return data, errors


def _build_routes_page_context(
    *,
    new_route_errors=None,
    new_route_form=None,
    open_modal="",
    route_vehicle_errors=None,
    route_vehicle_form=None,
    route_load_errors=None,
    route_load_form=None,
):
    routes = db.list_routes()
    locations_list = db.list_locations()
    locations_map = {l["location_id"]: l["name"] for l in locations_list}

    vehicles = db.list_vehicles()
    products = db.list_products()
    vehicles_map = {v["vehicle_id"]: v for v in vehicles}

    for r in routes:
        r["origin_name"] = locations_map.get(r["origin_location_id"], f"#{r['origin_location_id']}")
        r["dest_name"] = locations_map.get(r["dest_location_id"], f"#{r['dest_location_id']}")

        total_cost = 0.0
        for k in ["driver_cost", "load_cost", "unload_cost", "fuel_cost", "depreciation_cost", "insurance_cost"]:
            v = r.get(k)
            total_cost += float(v) if v is not None else 0.0
        r["total_cost"] = total_cost

        vid = r.get("vehicle_id")
        r["vehicle_name"] = vehicles_map.get(vid, {}).get("vehicle_name") if vid else None

        r["manifest_items"] = db.get_route_manifest(r["route_id"])
        r["manifest_count"] = len(r["manifest_items"])

    if new_route_form is None:
        new_route_form = {
            "name": "",
            "origin_location_id": "",
            "dest_location_id": "",
            "origin_address": "",
            "dest_address": "",
            "sales_amount": "",
            "vehicle_id": "",
            "driver_cost": "",
            "load_cost": "",
            "unload_cost": "",
            "fuel_cost": "",
            "depreciation_cost": "",
            "insurance_cost": "",
        }
    if new_route_errors is None:
        new_route_errors = {}

    return dict(
        routes=routes,
        locations=locations_list,
        vehicles=vehicles,
        products=products,
        new_route_errors=new_route_errors,
        new_route_form=new_route_form,
        open_modal=open_modal,
        route_vehicle_errors=route_vehicle_errors or {},
        route_vehicle_form=route_vehicle_form or {},
        route_load_errors=route_load_errors or {},
        route_load_form=route_load_form or {},
    )


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/")
def home():
    return redirect(url_for("routes_list"))


@app.get("/routes")
def routes_list():
    ctx = _build_routes_page_context()
    return render_template("routes_list.html", **ctx)


@app.post("/routes/new")
def route_new_post():
    data, errors = validate_route_form(request.form)

    if errors:
        new_route_form = {k: request.form.get(k, "") for k in [
            "name",
            "origin_location_id",
            "dest_location_id",
            "origin_address",
            "dest_address",
            "sales_amount",
            "vehicle_id",
            "driver_cost",
            "load_cost",
            "unload_cost",
            "fuel_cost",
            "depreciation_cost",
            "insurance_cost",
        ]}
        ctx = _build_routes_page_context(
            new_route_errors=errors,
            new_route_form=new_route_form,
            open_modal="modal-route",
        )
        return render_template("routes_list.html", **ctx), 400

    ok, err, new_id = db.create_route(**data)
    if not ok:
        abort(400)

    return redirect(url_for("routes_list"))


@app.post("/routes/<int:route_id>/assign-vehicle")
def route_assign_vehicle_post(route_id: int):
    route = db.get_route(route_id)
    if not route:
        abort(404)

    errors = {}
    vehicle_raw = (request.form.get("vehicle_id") or "").strip()

    vehicle_id = None
    if vehicle_raw:
        try:
            vehicle_id = int(vehicle_raw)
        except ValueError:
            errors["vehicle_id"] = "Choose a valid vehicle."

    if vehicle_id is not None and not db.get_vehicle(vehicle_id):
        errors["vehicle_id"] = "That vehicle does not exist."

    if errors:
        ctx = _build_routes_page_context(
            open_modal="modal-assign-vehicle",
            route_vehicle_errors={route_id: errors},
            route_vehicle_form={route_id: {"vehicle_id": vehicle_raw}},
        )
        return render_template("routes_list.html", **ctx), 400

    ok, err = db.assign_vehicle_to_route(route_id=route_id, vehicle_id=vehicle_id)
    if not ok:
        abort(400)

    return redirect(url_for("routes_list"))


@app.post("/routes/<int:route_id>/load/add")
def route_load_add_post(route_id: int):
    route = db.get_route(route_id)
    if not route:
        abort(404)

    errors = {}
    product_raw = (request.form.get("product_id") or "").strip()
    qty_raw = (request.form.get("quantity") or "").strip()

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
            quantity = int(qty_raw)
            if quantity <= 0:
                errors["quantity"] = "Quantity must be greater than 0."
        except ValueError:
            errors["quantity"] = "Quantity must be a whole number."

    if product_id is not None and not db.get_product(product_id):
        errors["product_id"] = "That product does not exist."

    if errors:
        ctx = _build_routes_page_context(
            open_modal="modal-manage-load",
            route_load_errors={route_id: errors},
            route_load_form={route_id: {"product_id": product_raw, "quantity": qty_raw}},
        )
        return render_template("routes_list.html", **ctx), 400

    ok, err = db.add_product_to_route(route_id=route_id, product_id=product_id, quantity=quantity)
    if not ok:
        abort(400)

    return redirect(url_for("routes_list"))


@app.post("/routes/<int:route_id>/load/remove")
def route_load_remove_post(route_id: int):
    route = db.get_route(route_id)
    if not route:
        abort(404)

    product_raw = (request.form.get("product_id") or "").strip()
    if not product_raw:
        abort(400)
    product_id = product_raw

    ok, err = db.remove_product_from_route(route_id=route_id, product_id=product_id)
    if not ok:
        abort(400)

    return redirect(url_for("routes_list"))


@app.get("/routes/<int:route_id>/edit")
def route_edit_get(route_id: int):
    route = db.get_route(route_id)
    if not route:
        abort(404)

    locations = db.list_locations()

    def _to_str(v):
        return "" if v is None else str(v)

    form_values = {
        "name": route.get("name", "") or "",
        "origin_location_id": _to_str(route.get("origin_location_id")),
        "dest_location_id": _to_str(route.get("dest_location_id")),
        "origin_address": route.get("origin_address", "") or "",
        "dest_address": route.get("dest_address", "") or "",
        "sales_amount": _to_str(route.get("base_sales_amount", route.get("sales_amount"))),
        "driver_cost": _to_str(route.get("driver_cost")),
        "load_cost": _to_str(route.get("load_cost")),
        "unload_cost": _to_str(route.get("unload_cost")),
        "fuel_cost": _to_str(route.get("fuel_cost")),
        "depreciation_cost": _to_str(route.get("depreciation_cost")),
        "insurance_cost": _to_str(route.get("insurance_cost")),
    }

    return render_template("route_edit.html", route=route, locations=locations, form_values=form_values, errors={})


@app.post("/routes/<int:route_id>/edit")
def route_edit_post(route_id: int):
    route = db.get_route(route_id)
    if not route:
        abort(404)

    locations = db.list_locations()
    data, errors = validate_route_form(request.form)

    if errors:
        form_values = {k: request.form.get(k, "") for k in [
            "name",
            "origin_location_id",
            "dest_location_id",
            "origin_address",
            "dest_address",
            "sales_amount",
            "driver_cost",
            "load_cost",
            "unload_cost",
            "fuel_cost",
            "depreciation_cost",
            "insurance_cost",
        ]}
        return render_template("route_edit.html", route=route, locations=locations, form_values=form_values, errors=errors), 400

    ok, err_code = db.update_route(
        route_id=route_id,
        name=data["name"],
        origin_location_id=data["origin_location_id"],
        dest_location_id=data["dest_location_id"],
        origin_address=data["origin_address"],
        dest_address=data["dest_address"],
        sales_amount=data["sales_amount"],
        driver_cost=data["driver_cost"],
        load_cost=data["load_cost"],
        unload_cost=data["unload_cost"],
        fuel_cost=data["fuel_cost"],
        depreciation_cost=data["depreciation_cost"],
        insurance_cost=data["insurance_cost"],
        vehicle_id=data.get("vehicle_id"),
    )

    if not ok:
        abort(400)

    return redirect(url_for("routes_list"))


# --------------------
# View Route (Details Page)
# --------------------

@app.get("/routes/<int:route_id>/view")
def route_view_get(route_id: int):
    route = db.get_route(route_id)
    if not route:
        abort(404)

    locations_list = db.list_locations()
    locations_map = {l["location_id"]: l["name"] for l in locations_list}

    route_view = dict(route)
    route_view["origin_name"] = locations_map.get(route.get("origin_location_id"), f"#{route.get('origin_location_id')}")
    route_view["dest_name"] = locations_map.get(route.get("dest_location_id"), f"#{route.get('dest_location_id')}")

    # total cost
    total_cost = 0.0
    for k in ["driver_cost", "load_cost", "unload_cost", "fuel_cost", "depreciation_cost", "insurance_cost"]:
        v = route.get(k)
        total_cost += float(v) if v is not None else 0.0
    route_view["total_cost"] = total_cost

    # vehicle details
    vehicle = None
    vid = route.get("vehicle_id")
    if vid is not None:
        vehicle = db.get_vehicle(vid)

    # manifest with pricing + subtotal
    manifest = []
    manifest_subtotal = 0.0

    for item in db.get_route_manifest(route_id):
        p = db.get_product(item["product_id"])
        unit_price = p.get("unit_price") if p else None

        try:
            unit_price_f = float(unit_price) if unit_price is not None else 0.0
        except (TypeError, ValueError):
            unit_price_f = 0.0

        try:
            qty = int(item.get("quantity", 0))
        except (TypeError, ValueError):
            qty = 0

        line_total = unit_price_f * qty
        manifest_subtotal += line_total

        manifest.append({
            "product_name": item["product_name"],
            "quantity": qty,
            "unit_price": unit_price_f if unit_price is not None else None,
            "line_total": line_total,
        })

    manifest.sort(key=lambda x: x["product_name"].lower())

    base_sales = route_view.get("base_sales_amount") or 0.0
    try:
        base_sales_f = float(base_sales)
    except (TypeError, ValueError):
        base_sales_f = 0.0

    return render_template(
        "route_view.html",
        route=route_view,
        vehicle=vehicle,
        manifest=manifest,
        manifest_subtotal=manifest_subtotal,
        base_sales=base_sales_f,
    )


# --------------------
# Products
# --------------------

@app.get("/products")
def products_list():
    products = db.list_products()
    return render_template("products_list.html", products=products)


@app.get("/products/new")
def product_new_get():
    return render_template(
        "product_form.html",
        mode="new",
        product=None,
        form_values={
            "product_name": "",
            "sku": "",
            "category": "",
            "unit": "",
            "unit_price": "",
        },
        errors={},
    )


@app.post("/products/new")
def product_new_post():
    data, errors = validate_product_form(request.form)
    if errors:
        form_values = {k: request.form.get(k, "") for k in ["product_name", "sku", "category", "unit", "unit_price"]}
        return render_template("product_form.html", mode="new", product=None, form_values=form_values, errors=errors), 400

    ok, err, new_id = db.create_product(**data)
    if not ok:
        abort(400)

    return redirect(url_for("products_list"))


@app.get("/products/<int:product_id>/edit")
def product_edit_get(product_id: int):
    product = db.get_product(product_id)
    if not product:
        abort(404)

    def _to_str(v):
        return "" if v is None else str(v)

    form_values = {
        "product_name": product.get("product_name", "") or "",
        "sku": product.get("sku", "") or "",
        "category": product.get("category", "") or "",
        "unit": product.get("unit", "") or "",
        "unit_price": _to_str(product.get("unit_price")),
    }
    return render_template("product_form.html", mode="edit", product=product, form_values=form_values, errors={})


@app.post("/products/<int:product_id>/edit")
def product_edit_post(product_id: int):
    product = db.get_product(product_id)
    if not product:
        abort(404)

    data, errors = validate_product_form(request.form)
    if errors:
        form_values = {k: request.form.get(k, "") for k in ["product_name", "sku", "category", "unit", "unit_price"]}
        return render_template("product_form.html", mode="edit", product=product, form_values=form_values, errors=errors), 400

    ok, err = db.update_product(product_id=product_id, **data)
    if not ok:
        abort(400)

    return redirect(url_for("products_list"))


# --------------------
# Vehicles + Locations (popup templates post here)
# --------------------

@app.post("/vehicles/new")
def vehicle_new_post():
    vehicle_name = (request.form.get("vehicle_name") or "").strip()
    mpg = (request.form.get("mpg") or "").strip()
    fuel_price = (request.form.get("fuel_price") or "").strip()
    capacity = (request.form.get("capacity") or "").strip()

    ok, err, new_id = db.create_vehicle(
        vehicle_name=vehicle_name,
        mpg=mpg,
        fuel_price=fuel_price,
        capacity=capacity,
    )
    if not ok:
        abort(400)

    return redirect(url_for("routes_list"))


@app.post("/locations/new")
def location_new_post():
    name = (request.form.get("name") or "").strip()
    region = (request.form.get("region") or "").strip()
    if not name:
        abort(400)

    ok, err, new_id = db.create_location(name=name, region=region)
    if not ok:
        abort(400)

    return redirect(url_for("routes_list"))


if __name__ == "__main__":
    app.run(debug=True)
