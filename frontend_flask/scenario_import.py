from flask import Blueprint, request, jsonify
import csv
import io
import access_db as db 
import logic           

from db.functions.tenant_functions import (
    scoped_read as read,
    scoped_create as create,
    scoped_update as update
)

from db.functions import scenario_management

scenario_import_bp = Blueprint(
    "scenario_import",
    __name__,
    url_prefix="/api/import/scenarios"
)

# Required headers for an exported routes CSV to be accepted
REQUIRED_HEADERS = {
    "scenario_id",
    "run_date",
    "route_name",
    "origin_name",
    "dest_name",
    "vehicle_name",
    "driver_name",
    "entered_revenue"
}

# Optional headers that may exist but are ignored during import
OPTIONAL_HEADERS = {
    "total_cost",
    "calculated_revenue",
    "profit_est_calculated",
    "margin_est_calculated",
}

# Full set of allowed CSV headers
ALLOWED_HEADERS = REQUIRED_HEADERS | OPTIONAL_HEADERS


def _lookup_by_name(view_fn, name):
    rows = view_fn()                     # Fetch all scoped rows
    for r in rows:
        if r.get("name") == name:        # Match by human-readable name
            return r
    return None


@scenario_import_bp.route("/upload", methods=["POST"])
def import_scenarios():

    if "file" not in request.files:      # Ensure file is present
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]

    if not file.filename.endswith(".csv"):  # Enforce CSV-only uploads
        return jsonify({"error": "CSV required"}), 400

    try:
        content = file.read().decode("utf-8")       # Read raw bytes
        reader = csv.DictReader(io.StringIO(content))  # Parse CSV rows
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    headers = set(reader.fieldnames or [])  # Extract CSV headers
    missing = REQUIRED_HEADERS - headers    # Required headers not present
    unexpected = headers - ALLOWED_HEADERS  # Headers not allowed

    if missing or unexpected:               # Reject invalid files early
        return jsonify({
            "status": "error",
            "missing_headers": sorted(missing),
            "unexpected_headers": sorted(unexpected)
        }), 400

    # Cache reference data once to avoid repeated DB queries
    locations = read.view_locations_scoped()
    vehicles  = read.view_vehicles_scoped()
    drivers   = read.view_drivers_scoped()
    routes    = read.view_routes_scoped()

    results = []

    for row_idx, row in enumerate(reader, start=2):  # start=2 matches CSV line numbers
        errors = []

        # Resolve names to database records
        origin  = next((l for l in locations if l["name"] == row["origin_name"]), None)
        dest    = next((l for l in locations if l["name"] == row["dest_name"]), None)
        vehicle = next((v for v in vehicles  if v["name"] == row["vehicle_name"]), None)
        driver  = next((d for d in drivers   if d["name"] == row["driver_name"]), None)
        route   = next((r for r in routes    if r["name"] == row["route_name"]), None)

        if not origin:
            errors.append(f"Origin not found: {row['origin_name']}")
        if not dest:
            errors.append(f"Destination not found: {row['dest_name']}")
        if not vehicle:
            errors.append(f"Vehicle not found: {row['vehicle_name']}")
        if not driver:
            errors.append(f"Driver not found: {row['driver_name']}")

        # Automatically create route if it does not already exist
        if not route and origin and dest:
            try:
                route_id = create.add_route_scoped(
                    name=row["route_name"],
                    origin_location_id=origin["location_id"],
                    dest_location_id=dest["location_id"]
                )
                route = {
                    "route_id": route_id,
                    "origin_location_id": origin["location_id"],
                    "dest_location_id": dest["location_id"],
                }
            except Exception as e:
                errors.append(str(e))

        if errors:  # Skip row safely if any validation fails
            results.append({
                "row": row_idx,
                "status": "error",
                "errors": errors
            })
            continue

        scenario_id = logic.safe_int(row["scenario_id"])        # Parse scenario ID
        revenue     = logic.safe_float(row["entered_revenue"], 0.0)  # Parse revenue

        existing = read.view_scenarios_scoped(ids=scenario_id)  # Check if scenario exists

        # Build header needed for distance and cost calculations
        calc_header = {
            "origin_address_street": origin.get("address_street"),
            "origin_city": origin.get("city"),
            "origin_state": origin.get("state"),
            "dest_address_street": dest.get("address_street"),
            "dest_city": dest.get("city"),
            "dest_state": dest.get("state")
        }

        # Calculate vehicle operating costs for this trip
        dep, ins, maint = logic.calculate_operating_costs(
            vehicle,
            logic.get_trip_length(calc_header)[0]
        )

        try:
            if existing:  # Update existing scenario snapshot
                scenario_management.update_scenario(
                    scenario_id=scenario_id,
                    total_revenue=revenue,
                    vehicle_id=vehicle["vehicle_id"],
                    driver_id=driver["driver_id"],
                    depreciation=dep,
                    daily_insurance=ins,
                    daily_maintenance=maint
                )
                action = "updated"
            else:  # Create new scenario if one does not exist
                scenario_id = scenario_management.create_scenario(
                    route_id=route["route_id"],
                    total_revenue=revenue,
                    vehicle_id=vehicle["vehicle_id"],
                    driver_id=driver["driver_id"],
                    depreciation=dep,
                    daily_insurance=ins,
                    daily_maintenance=maint
                )
                action = "created"

            results.append({
                "row": row_idx,
                "status": "success",
                "action": action,
                "scenario_id": scenario_id
            })

        except Exception as e:  # Catch and report per-row failure
            results.append({
                "row": row_idx,
                "status": "error",
                "errors": [str(e)]
            })

    return jsonify({
        "status": "completed",
        "results": results
    }), 200