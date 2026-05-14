from flask import Blueprint, request, jsonify, render_template
import csv
import io

from db.functions.tennant_functions import (
    scoped_read as read,
    scoped_create as create,
    scoped_update as update
)

routes_import_bp = Blueprint(
    "routes_import",
    __name__,
    url_prefix="/api/import/routes"
)

REQUIRED_HEADERS = {
    "name",
    "origin_name",
    "dest_name"
}


@routes_import_bp.route("/upload", methods=["GET"])
def routes_upload_form():
    return render_template(
        "simple_csv_upload.html",
        title="Route Import",
        post_url="/api/import/routes/upload"
    )


@routes_import_bp.route("/upload", methods=["POST"])
def import_routes():

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

    locations = read.view_locations_scoped()
    routes = read.view_routes_scoped()

    locations_by_name = {l["name"]: l for l in locations}
    routes_by_name = {r["name"]: r for r in routes}

    results = []

    for row_idx, row in enumerate(reader, start=2):
        errors = []

        name = row["name"].strip()
        origin_name = row["origin_name"]
        dest_name = row["dest_name"]

        if not name:
            errors.append("name is required")

        origin = locations_by_name.get(origin_name)
        dest = locations_by_name.get(dest_name)

        if not origin:
            errors.append(f"Origin not found: {origin_name}")
        if not dest:
            errors.append(f"Destination not found: {dest_name}")

        if errors:
            results.append({
                "row": row_idx,
                "status": "error",
                "errors": errors
            })
            continue

        payload = {
            "name": name,
            "origin_location_id": origin["location_id"],
            "dest_location_id": dest["location_id"]
        }

        try:
            if name in routes_by_name:
                update.update_route_scoped(
                    route_id=routes_by_name[name]["route_id"],
                    **payload
                )
                action = "updated"
                route_id = routes_by_name[name]["route_id"]
            else:
                route_id = create.add_route_scoped(**payload)
                action = "created"

            results.append({
                "row": row_idx,
                "status": "success",
                "action": action,
                "route_id": route_id
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