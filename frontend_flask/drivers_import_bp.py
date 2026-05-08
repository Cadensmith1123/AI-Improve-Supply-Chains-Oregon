from flask import Blueprint, request, jsonify, render_template
import csv
import io

from db.functions.tennant_functions import (
    scoped_read as read,
    scoped_create as create,
    scoped_update as update
)

drivers_import_bp = Blueprint(
    "drivers_import",
    __name__,
    url_prefix="/api/import/drivers"
)

REQUIRED_HEADERS = {
    "name",
    "hourly_drive_wage",
    "hourly_load_wage"
}


@drivers_import_bp.route("/upload", methods=["GET"])
def drivers_upload_form():
    return render_template(
        "simple_csv_upload.html",
        title="Driver Import",
        post_url="/api/import/drivers/upload"
    )


@drivers_import_bp.route("/upload", methods=["POST"])
def import_drivers():

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

    existing_drivers = read.view_drivers_scoped()
    existing_by_name = {d["name"]: d for d in existing_drivers}

    results = []

    for row_idx, row in enumerate(reader, start=2):
        errors = []

        name = row["name"].strip()

        try:
            hourly_drive = float(row["hourly_drive_wage"])
        except ValueError:
            errors.append("Invalid hourly_drive_wage")

        try:
            hourly_load = float(row["hourly_load_wage"])
        except ValueError:
            errors.append("Invalid hourly_load_wage")

        if not name:
            errors.append("name is required")

        if errors:
            results.append({
                "row": row_idx,
                "status": "error",
                "errors": errors
            })
            continue

        payload = {
            "name": name,
            "hourly_drive_wage": hourly_drive,
            "hourly_load_wage": hourly_load
        }

        try:
            if name in existing_by_name:
                update.update_driver_scoped(
                    driver_id=existing_by_name[name]["driver_id"],
                    **payload
                )
                action = "updated"
                driver_id = existing_by_name[name]["driver_id"]
            else:
                driver_id = create.add_driver_scoped(**payload)
                action = "created"

            results.append({
                "row": row_idx,
                "status": "success",
                "action": action,
                "driver_id": driver_id
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