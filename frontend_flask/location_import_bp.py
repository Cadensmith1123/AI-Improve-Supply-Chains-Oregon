from flask import Blueprint, request, jsonify, render_template
import csv
import io

from db.functions.tennant_functions import (
    scoped_read as read,
    scoped_create as create,
    scoped_update as update
)

location_import_bp = Blueprint(
    "location_import",
    __name__,
    url_prefix="/api/import/locations"
)

REQUIRED_HEADERS = {
    "name",
    "type",
    "address_street",
    "city",
    "state",
    "zip_code",
    "phone",
    "latitude",
    "longitude",
    "avg_load_minutes",
    "avg_unload_minutes"
}


@location_import_bp.route("/upload", methods=["GET"])
def location_upload_form():
    return render_template(
        "simple_csv_upload.html",
        title="Location Import",
        post_url="/api/import/locations/upload"
    )


@location_import_bp.route("/upload", methods=["POST"])
def import_locations():

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

    existing_locations = read.view_locations_scoped()
    existing_by_name = {l["name"]: l for l in existing_locations}

    results = []

    for row_idx, row in enumerate(reader, start=2):
        errors = []

        name = row["name"].strip()
        loc_type = row["type"]

        if not name:
            errors.append("name is required")

        if loc_type not in ("Hub", "Store", "Farm"):
            errors.append(f"Invalid type: {loc_type}")

        if errors:
            results.append({
                "row": row_idx,
                "status": "error",
                "errors": errors
            })
            continue

        payload = {
            "name": name,
            "type": loc_type,
            "address_street": row["address_street"],
            "city": row["city"],
            "state": row["state"],
            "zip_code": row["zip_code"],
            "phone": row["phone"],
            "latitude": row["latitude"],
            "longitude": row["longitude"],
            "avg_load_minutes": row["avg_load_minutes"],
            "avg_unload_minutes": row["avg_unload_minutes"],
        }

        try:
            if name in existing_by_name:
                update.update_location_scoped(
                    location_id=existing_by_name[name]["location_id"],
                    **payload
                )
                action = "updated"
                location_id = existing_by_name[name]["location_id"]
            else:
                location_id = create.add_location_scoped(**payload)
                action = "created"

            results.append({
                "row": row_idx,
                "status": "success",
                "action": action,
                "location_id": location_id
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