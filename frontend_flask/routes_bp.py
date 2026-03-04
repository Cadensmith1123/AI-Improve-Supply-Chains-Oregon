from flask import Blueprint, render_template, request, redirect, url_for, abort, jsonify, Response
import io
import access_db as db
import logic

"""
Manages route and scenario routes.
"""

routes_bp = Blueprint("routes", __name__)

def _get_route_response_data(route_id):
    """Helper to build JSON response with totals and enriched manifest."""
    route = db.get_route(route_id)
    if not route:
        return {"success": False, "message": "Route not found"}

    total_cost = route.get("calc_total_cost", 0.0)

    # Manifest is already enriched by db.get_route
    manifest = route.get("manifest", [])
    # Use the calculated revenue from the route header (calculated in logic.calculate_trip_costs)
    manifest_subtotal = route.get("calculated_revenue", 0.0)

    return {
        "success": True,
        "manifest": manifest,
        "manifest_subtotal": manifest_subtotal,
        "total_cost": total_cost,
        "entered_revenue": float(route.get("sales_amount") or 0.0),
        "sales_amount": float(route.get("sales_amount") or 0.0) + manifest_subtotal,
        "manifest_count": len(manifest)
    }


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
    drivers = db.list_drivers()
    vehicles_map = {v["vehicle_id"]: v for v in vehicles}
    products_map = {str(p["product_id"]): p for p in products}

    for r in routes:
        r["origin_name"] = locations_map.get(r["origin_location_id"], f"#{r['origin_location_id']}")
        r["dest_name"] = locations_map.get(r["dest_location_id"], f"#{r['dest_location_id']}")

        full_route = db.get_route(r["route_id"])
        r["total_cost"] = full_route.get("calc_total_cost", 0.0) if full_route else 0.0
        r["manifest_items"] = []
        
        if full_route:
            r["fuel_cost"] = full_route.get("fuel_cost", 0.0)
            r["depreciation_cost"] = full_route.get("depreciation_cost", 0.0)

            # Use values already calculated in full_route to avoid N+1 manifest fetch and loop
            r["manifest_count"] = full_route.get("line_item_count", 0)
            manifest_subtotal = full_route.get("calculated_revenue", 0.0)
            
            r["item_revenue"] = manifest_subtotal
            r["sales_amount"] = float(r.get("sales_amount") or 0) + manifest_subtotal
            r["manifest_items"] = full_route.get("manifest", [])

        vid = r.get("vehicle_id")
        r["vehicle_name"] = vehicles_map.get(vid, {}).get("vehicle_name") if vid else None

    if new_route_form is None:
        new_route_form = {
            "name": "",
            "origin_location_id": "",
            "dest_location_id": "",
            "origin_address": "",
            "dest_address": "",
            "sales_amount": "",
            "vehicle_id": "",
            "driver_id": "",
            "gas_price": "",
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
        drivers=drivers,
        new_route_errors=new_route_errors,
        new_route_form=new_route_form,
        open_modal=open_modal,
        route_vehicle_errors=route_vehicle_errors or {},
        route_vehicle_form=route_vehicle_form or {},
        route_load_errors=route_load_errors or {},
        route_load_form=route_load_form or {},
    )

@routes_bp.get("/routes")
def routes_list():
    ctx = _build_routes_page_context()
    return render_template("routes_list.html", **ctx)


@routes_bp.get("/routes/export")
def routes_export_csv():
    all_details = db.get_all_routes_raw()
    
    si = io.StringIO()
    db.export_routes_csv(all_details, si)
    output = si.getvalue()
    
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=all_routes.csv"}
    )

@routes_bp.get("/routes/<int:route_id>/export")
def route_export_csv(route_id):
    details = db.get_route_raw(route_id)
    if not details:
        abort(404)
        
    si = io.StringIO()
    db.export_route_detailed_csv(details, si)
    output = si.getvalue()
    
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-disposition": f"attachment; filename=route_{route_id}.csv"}
    )

@routes_bp.post("/routes/new")
def route_new_post():
    data, errors = logic.validate_route_form(request.form)

    if errors:
        new_route_form = {k: request.form.get(k, "") for k in [
            "name",
            "origin_location_id",
            "dest_location_id",
            "sales_amount",
            "vehicle_id",
            "driver_id",
            "gas_price",
        ]}
        ctx = _build_routes_page_context(
            new_route_errors=errors,
            new_route_form=new_route_form,
            open_modal="modal-route",
        )
        return render_template("routes_list.html", **ctx), 400

    ok, err, new_id = db.create_route(**data)
    if not ok:
        abort(400, description=f"Failed to create route: {err}")

    return redirect(url_for("routes.routes_list"))


@routes_bp.post("/routes/<int:route_id>/delete")
def route_delete_post(route_id: int):
    ok, err = db.delete_route(route_id)
    if not ok:
        return jsonify({"success": False, "message": err}), 400
    return jsonify({"success": True})


@routes_bp.post("/routes/<int:route_id>/recalc")
def route_recalc_post(route_id: int):
    ok, err = db.recalculate_route_costs(route_id)
    if not ok:
        return jsonify({"success": False, "message": err}), 400
    return jsonify({"success": True})


@routes_bp.post("/routes/<int:route_id>/assign-vehicle")
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
        abort(400, description=f"Failed to assign vehicle: {err}")

    if request.referrer and "view" in request.referrer:
        return redirect(url_for("routes.route_view_get", route_id=route_id))

    return redirect(url_for("routes.routes_list"))


@routes_bp.post("/routes/<int:route_id>/assign-driver")
def route_assign_driver_post(route_id: int):
    route = db.get_route(route_id)
    if not route:
        abort(404)

    driver_raw = (request.form.get("driver_id") or "").strip()
    driver_id = int(driver_raw) if driver_raw else None

    ok, err = db.assign_driver_to_route(route_id=route_id, driver_id=driver_id)
    if not ok:
        abort(400, description=f"Failed to assign driver: {err}")

    if request.referrer and "view" in request.referrer:
        return redirect(url_for("routes.route_view_get", route_id=route_id))

    return redirect(url_for("routes.routes_list"))


@routes_bp.post("/routes/<int:route_id>/load/add")
def route_load_add_post(route_id: int):
    route = db.get_route(route_id)
    if not route:
        abort(404)

    data, errors = logic.validate_load_form(request.form)

    if data["product_id"] is not None and not db.get_product(data["product_id"]):
        errors["product_id"] = "That product does not exist."

    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    if errors:
        if is_ajax:
            return jsonify({"success": False, "errors": errors}), 400

        form_data = {k: request.form.get(k, "") for k in [
            "product_id", "quantity", "price_per_item", 
            "items_per_unit", "cost_per_item", "unit_weight", "unit_volume"
        ]}

        ctx = _build_routes_page_context(
            open_modal="modal-manage-load",
            route_load_errors={route_id: errors},
            route_load_form={route_id: form_data},
        )
        return render_template("routes_list.html", **ctx), 400

    ok, err = db.add_product_to_route(
        route_id=route_id, 
        product_id=data["product_id"], 
        quantity=data["quantity"],
        price_per_item=data["price_per_item"],
        items_per_unit=data["items_per_unit"],
        cost_per_item=data["cost_per_item"],
        unit_weight=data["unit_weight"],
        unit_volume=data["unit_volume"]
    )
    
    if is_ajax:
        if not ok:
            return jsonify({"success": False, "message": err}), 400
        return jsonify(_get_route_response_data(route_id))

    if not ok:
        abort(400)

    return redirect(url_for("routes.routes_list"))


@routes_bp.post("/routes/<int:route_id>/load/remove")
def route_load_remove_post(route_id: int):
    route = db.get_route(route_id)
    if not route:
        abort(404)

    product_raw = (request.form.get("product_id") or "").strip()
    if not product_raw:
        abort(400)
    product_id = product_raw

    ok, err = db.remove_product_from_route(route_id=route_id, product_id=product_id)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        if not ok:
            return jsonify({"success": False, "message": err}), 400
        return jsonify(_get_route_response_data(route_id))

    if not ok:
        abort(400)

    return redirect(url_for("routes.routes_list"))


@routes_bp.get("/routes/<int:route_id>/edit")
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


@routes_bp.post("/routes/<int:route_id>/edit")
def route_edit_post(route_id: int):
    route = db.get_route(route_id)
    if not route:
        abort(404)

    locations = db.list_locations()
    data, errors = logic.validate_route_form(request.form)

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
        driver_id=data.get("driver_id"),
    )

    if not ok:
        abort(400)

    return redirect(url_for("routes.routes_list"))


@routes_bp.get("/routes/<int:route_id>/view")
def route_view_get(route_id: int):
    route = db.get_route(route_id)
    if not route:
        abort(404)

    vehicles = db.list_vehicles()
    products = db.list_products()
    drivers = db.list_drivers()
    routes_list = db.list_routes()

    locations_list = db.list_locations()
    locations_map = {l["location_id"]: l["name"] for l in locations_list}
    locations_objs = {l["location_id"]: l for l in locations_list}

    route_view = dict(route)
    route_view["origin_name"] = locations_map.get(route.get("origin_location_id"), f"#{route.get('origin_location_id')}")
    route_view["dest_name"] = locations_map.get(route.get("dest_location_id"), f"#{route.get('dest_location_id')}")

    total_cost = route.get("calc_total_cost", 0.0)
    route_view["total_cost"] = total_cost

    vehicle = None
    vid = route.get("vehicle_id")
    if vid is not None:
        vehicle = db.get_vehicle(vid)

    driver = None
    did = route.get("driver_id")
    if did is not None:
        driver = db.get_driver(did)

    # Manifest is already enriched by db.get_route
    manifest = route.get("manifest", [])
    # Use the calculated revenue from the route header
    manifest_subtotal = route.get("calculated_revenue", 0.0)

    base_sales = route_view.get("base_sales_amount") or 0.0
    try:
        base_sales_f = float(base_sales)
    except (TypeError, ValueError):
        base_sales_f = 0.0

    return render_template(
        "route_view.html",
        route=route_view,
        vehicle=vehicle,
        driver=driver,
        manifest=manifest,
        manifest_subtotal=manifest_subtotal,
        base_sales=base_sales_f,
        origin=locations_objs.get(route.get("origin_location_id")),
        destination=locations_objs.get(route.get("dest_location_id")),
        vehicles=vehicles,
        products=products,
        drivers=drivers,
        locations=locations_list,
        routes=routes_list,
        new_route_form={},
        new_route_errors={},
    )