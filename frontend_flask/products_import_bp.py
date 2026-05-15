from flask import Blueprint, request, jsonify, render_template
import csv
import io

from db.functions.tenant_functions import (
    scoped_read as read,
    scoped_create as create,
    scoped_update as update
)

products_import_bp = Blueprint(
    "products_import",
    __name__,
    url_prefix="/api/import/products"
)

REQUIRED_HEADERS = {
    "product_code",
    "name",
    "storage_type"
}


@products_import_bp.route("/upload", methods=["GET"])
def products_upload_form():
    return render_template(
        "simple_csv_upload.html",
        title="Product Import",
        post_url="/api/import/products/upload"
    )


@products_import_bp.route("/upload", methods=["POST"])
def import_products():

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

    existing_products = read.view_products_master_scoped()
    existing_by_code = {
        p["product_code"]: p for p in existing_products
    }

    results = []

    for row_idx, row in enumerate(reader, start=2):
        errors = []

        product_code = row["product_code"].strip()
        name = row["name"].strip()
        storage_type = row["storage_type"]

        if not product_code:
            errors.append("product_code is required")

        if not name:
            errors.append("name is required")

        if storage_type not in ("Dry", "Ref", "Frz"):
            errors.append(f"Invalid storage_type: {storage_type}")

        if errors:
            results.append({
                "row": row_idx,
                "status": "error",
                "errors": errors
            })
            continue

        payload = {
            "product_code": product_code,
            "name": name,
            "storage_type": storage_type
        }

        try:
            if product_code in existing_by_code:
                update.update_product_master_scoped(**payload)
                action = "updated"
            else:
                create.add_product_master_scoped(**payload)
                action = "created"

            results.append({
                "row": row_idx,
                "status": "success",
                "action": action,
                "product_code": product_code
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