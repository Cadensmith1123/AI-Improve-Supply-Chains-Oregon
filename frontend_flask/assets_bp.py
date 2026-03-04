from flask import Blueprint, request, redirect, url_for, abort, jsonify
import access_db as db

"""
Manages user asset (vehicles, and drivers) endpoints.
"""

assets_bp = Blueprint("assets", __name__)

@assets_bp.post("/vehicles/new")
def vehicle_new_post():
    vehicle_name = (request.form.get("vehicle_name") or "").strip()
    mpg = (request.form.get("mpg") or "").strip()
    capacity = (request.form.get("capacity") or "").strip()
    purchase_price = (request.form.get("purchase_price") or "").strip()
    yearly_mileage = (request.form.get("yearly_mileage") or "").strip()
    salvage_value = (request.form.get("salvage_value") or "").strip()
    insurance_cost = (request.form.get("insurance_cost") or "").strip()
    maintenance_cost = (request.form.get("maintenance_cost") or "").strip()
    storage_type = (request.form.get("storage_type") or "Dry").strip()

    ok, err, new_id = db.create_vehicle(
        vehicle_name=vehicle_name,
        mpg=mpg,
        capacity=capacity,
        purchase_price=purchase_price,
        yearly_mileage=yearly_mileage,
        salvage_value=salvage_value,
        insurance_cost=insurance_cost,
        maintenance_cost=maintenance_cost,
        storage_type=storage_type
    )
    if not ok:
        abort(400)

    return redirect(url_for("routes.routes_list"))


@assets_bp.post("/vehicles/<int:vehicle_id>/edit")
def vehicle_edit_post(vehicle_id: int):
    vehicle_name = (request.form.get("vehicle_name") or "").strip()
    mpg = (request.form.get("mpg") or "").strip()
    capacity = (request.form.get("capacity") or "").strip()
    purchase_price = (request.form.get("purchase_price") or "").strip()
    yearly_mileage = (request.form.get("yearly_mileage") or "").strip()
    salvage_value = (request.form.get("salvage_value") or "").strip()
    insurance_cost = (request.form.get("insurance_cost") or "").strip()
    maintenance_cost = (request.form.get("maintenance_cost") or "").strip()
    storage_type = (request.form.get("storage_type") or "Dry").strip()

    ok, err = db.update_vehicle(
        vehicle_id=vehicle_id, 
        vehicle_name=vehicle_name, 
        mpg=mpg, 
        capacity=capacity,
        purchase_price=purchase_price,
        yearly_mileage=yearly_mileage,
        salvage_value=salvage_value,
        insurance_cost=insurance_cost,
        maintenance_cost=maintenance_cost,
        storage_type=storage_type
    )
    if not ok:
        abort(400)
    return redirect(url_for("routes.routes_list"))


@assets_bp.post("/vehicles/<int:vehicle_id>/delete")
def vehicle_delete_post(vehicle_id: int):
    ok, err = db.delete_vehicle(vehicle_id)
    if not ok:
        return jsonify({"success": False, "message": err}), 400
    return jsonify({"success": True})


@assets_bp.post("/locations/new")
def location_new_post():
    name = (request.form.get("name") or "").strip()
    loc_type = (request.form.get("type") or "Hub").strip()
    address = (request.form.get("address_street") or "").strip()
    city = (request.form.get("city") or "").strip()
    state = (request.form.get("state") or "").strip()
    zip_code = (request.form.get("zip_code") or "").strip()
    phone = (request.form.get("phone") or "").strip()
    load_mins = (request.form.get("avg_load_minutes") or "").strip()
    unload_mins = (request.form.get("avg_unload_minutes") or "").strip()

    if not name:
        abort(400)

    ok, err, new_id = db.create_location(
        name=name,
        loc_type=loc_type,
        address=address,
        city=city,
        state=state,
        zip_code=zip_code,
        phone=phone,
        avg_load_minutes=load_mins,
        avg_unload_minutes=unload_mins
    )
    if not ok:
        abort(400)

    return redirect(url_for("routes.routes_list"))


@assets_bp.post("/locations/<int:location_id>/edit")
def location_edit_post(location_id: int):
    name = (request.form.get("name") or "").strip()
    loc_type = (request.form.get("type") or "Hub").strip()
    address = (request.form.get("address_street") or "").strip()
    city = (request.form.get("city") or "").strip()
    state = (request.form.get("state") or "").strip()
    zip_code = (request.form.get("zip_code") or "").strip()
    phone = (request.form.get("phone") or "").strip()
    load_mins = (request.form.get("avg_load_minutes") or "").strip()
    unload_mins = (request.form.get("avg_unload_minutes") or "").strip()
    
    ok, err = db.update_location(
        location_id=location_id,
        name=name,
        loc_type=loc_type,
        address=address,
        city=city,
        state=state,
        zip_code=zip_code,
        phone=phone,
        avg_load_minutes=load_mins,
        avg_unload_minutes=unload_mins
    )
    if not ok:
        abort(400)
    return redirect(url_for("routes.routes_list"))


@assets_bp.post("/locations/<int:location_id>/delete")
def location_delete_post(location_id: int):
    ok, err = db.delete_location(location_id)
    if not ok:
        return jsonify({"success": False, "message": err}), 400
    return jsonify({"success": True})


@assets_bp.post("/drivers/new")
def driver_new_post():
    name = (request.form.get("name") or "").strip()
    hourly_drive_wage = (request.form.get("hourly_drive_wage") or "").strip()
    hourly_load_wage = (request.form.get("hourly_load_wage") or "").strip()

    if not name:
        abort(400)

    ok, err, new_id = db.create_driver(name, hourly_drive_wage, hourly_load_wage)
    if not ok:
        abort(400)
    return redirect(url_for("routes.routes_list"))


@assets_bp.post("/drivers/<int:driver_id>/delete")
def driver_delete_post(driver_id: int):
    ok, err = db.delete_driver(driver_id)
    if not ok:
        return jsonify({"success": False, "message": err}), 400
    return jsonify({"success": True})


@assets_bp.post("/drivers/<int:driver_id>/edit")
def driver_edit_post(driver_id: int):
    name = (request.form.get("name") or "").strip()
    hourly_drive_wage = (request.form.get("hourly_drive_wage") or "").strip()
    hourly_load_wage = (request.form.get("hourly_load_wage") or "").strip()

    ok, err = db.update_driver(driver_id, name, hourly_drive_wage, hourly_load_wage)
    if not ok:
        abort(400)
    return redirect(url_for("routes.routes_list"))