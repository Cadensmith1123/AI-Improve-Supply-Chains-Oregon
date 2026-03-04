from flask import Blueprint, render_template, request, redirect, url_for, abort, jsonify
import access_db as db
import logic

"""
Manages the products routes.
"""

products_bp = Blueprint("products", __name__)

@products_bp.get("/products")
def products_list():
    products = db.list_products()
    return render_template("products_list.html", products=products)


@products_bp.get("/products/new")
def product_new_get():
    return render_template(
        "product_form.html",
        mode="new",
        product=None,
        form_values={
            "product_name": "",
            "sku": "",
            "storage_type": "Dry",
        },
        errors={},
    )


@products_bp.post("/products/new")
def product_new_post():
    data, errors = logic.validate_product_form(request.form)
    if errors:
        form_values = {k: request.form.get(k, "") for k in ["product_name", "sku", "storage_type"]}
        return render_template("product_form.html", mode="new", product=None, form_values=form_values, errors=errors), 400

    ok, err, new_id = db.create_product(**data)
    if not ok:
        abort(400)
    return redirect(request.form.get("next") or url_for("products.products_list"))

@products_bp.post("/products/<product_id>/delete")
def product_delete_post(product_id):
    ok, err = db.delete_product(product_id)
    if not ok:
        return jsonify({"success": False, "message": err}), 400
    return jsonify({"success": True})


@products_bp.get("/products/<product_id>/edit")
def product_edit_get(product_id):
    product = db.get_product(product_id)
    if not product:
        abort(404)

    def _to_str(v):
        return "" if v is None else str(v)

    form_values = {
        "product_name": product.get("product_name", "") or "",
        "sku": product.get("sku", "") or "",
        "storage_type": product.get("storage_type", "") or "Dry",
    }
    return render_template("product_form.html", mode="edit", product=product, form_values=form_values, errors={})


@products_bp.post("/products/<product_id>/edit")
def product_edit_post(product_id):
    product = db.get_product(product_id)
    if not product:
        abort(404)

    data, errors = logic.validate_product_form(request.form)
    if errors:
        form_values = {k: request.form.get(k, "") for k in ["product_name", "sku", "storage_type"]}
        return render_template("product_form.html", mode="edit", product=product, form_values=form_values, errors=errors), 400

    ok, err = db.update_product(product_id=product_id, product_name=data["product_name"], storage_type=data["storage_type"])
    if not ok:
        abort(400)

    return redirect(request.form.get("next") or url_for("products.products_list"))