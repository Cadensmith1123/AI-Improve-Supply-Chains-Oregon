import io
import csv
from flask import Blueprint, make_response, abort

csv_template_bp = Blueprint(
    "csv_templates",
    __name__,
    url_prefix="/api/import/templates"
)

CSV_TEMPLATES = {
    "locations": [
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
        "avg_unload_minutes",
    ],
    "products": [
        "product_code",
        "name",
        "storage_type",
    ],
    "drivers": [
        "name",
        "hourly_drive_wage",
        "hourly_load_wage",
    ],
    "vehicles": [
        "name",
        "mpg",
        "vehicle_purchase_price",
        "vehicle_estimated_yearly_milage",
        "vehicle_estimated_salvage_value",
        "annual_insurance_cost",
        "annual_maintenance_cost",
        "max_weight_lbs",
        "max_volume_cubic_ft",
        "storage_type",
    ],
    "routes": [
        "name",
        "origin_name",
        "dest_name",
    ],
}


@csv_template_bp.get("/<asset_type>")
def download_csv_template(asset_type):
    headers = CSV_TEMPLATES.get(asset_type)

    if not headers:
        abort(404, f"No CSV template defined for '{asset_type}'")

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)

    response = make_response(output.getvalue())
    response.headers["Content-Type"] = "text/csv"
    response.headers["Content-Disposition"] = (
        f'attachment; filename="{asset_type}_template.csv"'
    )

    return response