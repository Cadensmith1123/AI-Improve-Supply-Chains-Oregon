from flask import Flask, render_template, request, redirect, url_for, abort
import db

app = Flask(__name__)

def validate_route_form(form):
    errors = {}

    name = (form.get("name") or "").strip()
    origin_raw = (form.get("origin_location_id") or "").strip()
    dest_raw = (form.get("dest_location_id") or "").strip()
    sales_raw = (form.get("sales_amount") or "").strip()

    # Required checks
    if not origin_raw:
        errors["origin_location_id"] = "Start is required."
    if not dest_raw:
        errors["dest_location_id"] = "Destination is required."
    if not sales_raw:
        errors["sales_amount"] = "Sales amount is required."

    origin_id = None
    dest_id = None
    sales_amount = None

    if origin_raw:
        try:
            origin_id = int(origin_raw)
        except ValueError:
            errors["origin_location_id"] = "Start must be a valid location."

    if dest_raw:
        try:
            dest_id = int(dest_raw)
        except ValueError:
            errors["dest_location_id"] = "Destination must be a valid location."

    # Non-numeric validation
    if sales_raw:
        try:
            sales_amount = float(sales_raw)
        except ValueError:
            errors["sales_amount"] = "Sales amount must be numeric (e.g., 1200.50)."

    # Optional: start != destination
    if origin_id is not None and dest_id is not None and origin_id == dest_id:
        errors["dest_location_id"] = "Destination must be different from start."

    data = {
        "name": name,
        "origin_location_id": origin_id,
        "dest_location_id": dest_id,
        "sales_amount": sales_amount,
    }
    return data, errors


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/routes")
def routes_list():
    routes = db.list_routes()
    locations = {l["location_id"]: l["name"] for l in db.list_locations()}

    for r in routes:
        r["origin_name"] = locations.get(r["origin_location_id"], f"#{r['origin_location_id']}")
        r["dest_name"] = locations.get(r["dest_location_id"], f"#{r['dest_location_id']}")

    return render_template("routes_list.html", routes=routes)


@app.get("/routes/<int:route_id>/edit")
def route_edit_get(route_id: int):
    route = db.get_route(route_id)
    if not route:
        abort(404)

    locations = db.list_locations()

    form_values = {
        "name": route.get("name", "") or "",
        "origin_location_id": str(route.get("origin_location_id", "") or ""),
        "dest_location_id": str(route.get("dest_location_id", "") or ""),
        "sales_amount": "" if route.get("sales_amount") is None else str(route.get("sales_amount")),
    }

    return render_template(
        "route_edit.html",
        route=route,
        locations=locations,
        form_values=form_values,
        errors={}
    )


@app.post("/routes/<int:route_id>/edit")
def route_edit_post(route_id: int):
    route = db.get_route(route_id)
    if not route:
        abort(404)

    locations = db.list_locations()
    data, errors = validate_route_form(request.form)

    if errors:
        form_values = {
            "name": request.form.get("name", ""),
            "origin_location_id": request.form.get("origin_location_id", ""),
            "dest_location_id": request.form.get("dest_location_id", ""),
            "sales_amount": request.form.get("sales_amount", ""),
        }
        return render_template(
            "route_edit.html",
            route=route,
            locations=locations,
            form_values=form_values,
            errors=errors
        ), 400

    ok, err_code = db.update_route(
        route_id=route_id,
        name=data["name"],
        origin_location_id=data["origin_location_id"],
        dest_location_id=data["dest_location_id"],
        sales_amount=data["sales_amount"],
    )

    if not ok:
        abort(400)

    return redirect(url_for("routes_list"))


if __name__ == "__main__":
    app.run(debug=True)
