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


def _build_routes_page_context(**kwargs):
    """
    Prepares all the data needed to display the 'Routes' page.

    This function does two main things:
    1. Fetches the background data (list of routes, vehicles, drivers) so the dashboard looks complete.
    2. Handles form errors. If a user tries to create a route but forgets a field, this function 
       ensures their typed data isn't lost and tells the page to keep the popup window open 
       so they can see the error message.

    Args:
        **kwargs: Optional overrides. For example, if there is an error, we pass in the 
                  specific error message and the data the user tried to submit.
    """
    # 1. Fetch the base data required for the dashboard (lists of routes, vehicles, etc.)
    ctx = db.get_dashboard_data()

    # 2. Define the default "clean slate" for the new route form. This is used when
    #    the page is first loaded (a GET request) or when a form is successfully submitted.
    default_new_route = {
        "name": "", "origin_location_id": "", "dest_location_id": "",
        "origin_address": "", "dest_address": "", "sales_amount": "",
        "vehicle_id": "", "driver_id": "", "gas_price": "",
        "driver_cost": "", "load_cost": "", "unload_cost": "",
        "fuel_cost": "", "depreciation_cost": "", "insurance_cost": "",
    }

    # 3. Merge the base data with any UI state overrides passed via kwargs.
    #    If a kwarg is not provided (e.g., on a simple GET request).
    #    This keeps the template rendering logic simple.
    ctx.update({
        "new_route_form": kwargs.get("new_route_form") or default_new_route,
        "new_route_errors": kwargs.get("new_route_errors") or {},
        "open_modal": kwargs.get("open_modal", ""),
        "route_vehicle_errors": kwargs.get("route_vehicle_errors") or {},
        "route_vehicle_form": kwargs.get("route_vehicle_form") or {},
        "route_load_errors": kwargs.get("route_load_errors") or {},
        "route_load_form": kwargs.get("route_load_form") or {},
    })
    
    # 4. Return the complete context dictionary, ready to be passed to the template.
    return ctx

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

    ok, err, new_id = db.create_route(
        name=data["name"],
        origin_location_id=data["origin_location_id"],
        dest_location_id=data["dest_location_id"],
        sales_amount=data["sales_amount"],
        vehicle_id=data["vehicle_id"],
        driver_id=data["driver_id"],
        gas_price=data["gas_price"]
    )
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
        sales_amount=data["sales_amount"],
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