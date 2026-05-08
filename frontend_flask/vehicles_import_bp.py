from flask import Blueprint, request, jsonify, render_template
import csv
import io

from db.functions.tennant_functions import (
    scoped_read as read,
    scoped_create as create,
    scoped_update as update
)

vehicles_import_bp = Blueprint(
    "vehicles_import",
    __name__,
    url_prefix="/api/import/vehicles"
)

REQUIRED_HEADERS = {
    "name",
    "mpg",
    "vehicle_purchase_price",
    "vehicle_estimated_yearly_milage",
    "vehicle_estimated_salvage_value",
    "annual_insurance_cost",
    "annual_maintenance_cost",
    "max_weight_lbs",
    "max_volume_cubic_ft",
    "storage_type"
}


@vehicles_import_bp.route("/upload", methods=["GET"])
def vehicles_upload_form():
    return render_template(
        "simple_csv_upload.html",
        title="Vehicle Import",
        post_url="/api/import/vehicles/upload"
    )


@vehicles_import_bp.route("/upload", methods=["POST"])
def import_vehicles():

    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    if not file.filename.endswith(".csv"):
        return jsonify({"error": "CSV required"}), 400

    try:
        content = file.read().decode("utf-8")
        reader = csv.DictReader(io.StringIO(content))
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    headers = set(reader.fieldnames or [])

    missing = REQUIRED_HEADERS - headers
    unexpected = headers - REQUIRED_HEADERS

    if missing or unexpected:
        return jsonify({
            "status": "error",
            "missing_headers": sorted(missing),
            "unexpected_headers": sorted(unexpected)
        }), 400

    existing_vehicles = read.view_vehicles_scoped()
    existing_by_name = {v["name"]: v for v in existing_vehicles}

    results = []

    for row_idx, row in enumerate(reader, start=2):
        errors = []

        name = row["name"].strip()
        storage_type = row["storage_type"]

        if not name:
            errors.append("name is required")

        if storage_type not in ("Dry", "Ref", "Frz", "Multi"):
            errors.append(f"Invalid storage_type: {storage_type}")

        # Numeric parsing / validation
        def parse_float(field):
            try:
                return float(row[field])
            except ValueError:
                errors.append(f"Invalid {field}")
                return None

        mpg = parse_float("mpg")
        purchase_price = parse_float("vehicle_purchase_price")
        yearly_miles = parse_float("vehicle_estimated_yearly_milage")
        salvage_value = parse_float("vehicle_estimated_salvage_value")
        insurance = parse_float("annual_insurance_cost")
        maintenance = parse_float("annual_maintenance_cost")
        max_weight = parse_float("max_weight_lbs")
        max_volume = parse_float("max_volume_cubic_ft")

        if errors:
            results.append({
                "row": row_idx,
                "status": "error",
                "errors": errors
            })
            continue

        payload = {
            "name": name,
            "mpg": mpg,
            "vehicle_purchase_price": purchase_price,
            "vehicle_estimated_yearly_milage": yearly_miles,
            "vehicle_estimated_salvage_value": salvage_value,
            "annual_insurance_cost": insurance,
            "annual_maintenance_cost": maintenance,
            "max_weight_lbs": max_weight,
            "max_volume_cubic_ft": max_volume,
            "storage_type": storage_type
        }

        try:
            if name in existing_by_name:
                update.update_vehicle_scoped(
                    vehicle_id=existing_by_name[name]["vehicle_id"],
                    **payload
                )
                action = "updated"
                vehicle_id = existing_by_name[name]["vehicle_id"]
            else:
                vehicle_id = create.add_vehicle_scoped(**payload)
                action = "created"

            results.append({
                "row": row_idx,
                "status": "success",
                "action": action,
                "vehicle_id": vehicle_id
            })

        except Exception as e:
            results.append({
                "row": row_idx,
                "status": "error",
                "errors": [str(e)]
            })

    return jsonify({
        "status": "completed",
        "results": results
    }), 200