import os
from flask import Flask, render_template, request, redirect, url_for, abort, flash
import urllib.parse
import requests
from typing import Tuple
import db

from dotenv import load_dotenv 

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "change")

MAPBOX_TOKEN = os.getenv("MAPBOX_TOKEN")
if not MAPBOX_TOKEN:
    raise RuntimeError("MAPBOX_TOKEN is not set. Define it in your environment or .env")

GEOCODE_ENDPOINT = "https://api.mapbox.com/geocoding/v5/mapbox.places/{query}.json"
_session = requests.Session()

def geocode_address(address: str) -> Tuple[float, float, str]:
    address = (address or "").strip()
    if not address:
        raise ValueError("Address cannot be empty.")

    params = {
        "access_token": MAPBOX_TOKEN,
        "limit": 1,
        "autocomplete": "false",
        "types": "address,poi,place",
    }

    url = GEOCODE_ENDPOINT.format(query=urllib.parse.quote(address))

    try:
        response = _session.get(url, params=params, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        raise RuntimeError("Geocoding request failed") from e

    data = response.json()
    features = data.get("features")

    if not features:
        raise ValueError(f"No geocoding match found for: {address}")

    feature = features[0]
    try:
        lon, lat = feature["center"]
    except (KeyError, ValueError):
        raise RuntimeError("Unexpected geocoding response format")

    place_name = feature.get("place_name", address)
    return lon, lat, place_name

@app.route("/", methods=["GET"])
def index():
    args = {
        "start": request.args.get("start", "") or "",
        "end": request.args.get("end", "") or "",
        "start_lng": request.args.get("start_lng"),
        "start_lat": request.args.get("start_lat"),
        "end_lng": request.args.get("end_lng"),
        "end_lat": request.args.get("end_lat"),
    }
    args = {k: v for k, v in args.items() if v is not None}
    return redirect(url_for("routes_list", **args))

@app.route("/calculate_route", methods=["POST"])
def route():
    start_query = request.form.get("start", "").strip()
    end_query = request.form.get("end", "").strip()

    if not start_query or not end_query:
        flash("Please enter both start and end addresses.", "error")
        return redirect(url_for("index", start=start_query, end=end_query))

    try:
        s_lon, s_lat, s_label = geocode_address(start_query)
        e_lon, e_lat, e_label = geocode_address(end_query)
    except Exception as e:
        flash(str(e), "error")
        return redirect(url_for("index", start=start_query, end=end_query))

    return redirect(url_for(
        "index",
        start=s_label,
        end=e_label,
        start_lng=s_lon,
        start_lat=s_lat,
        end_lng=e_lon,
        end_lat=e_lat
    ))
# === End moved block ===


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


@app.get("/routes/")
def routes_list():
    routes = db.list_routes()
    locations = {l["location_id"]: l["name"] for l in db.list_locations()}

    for r in routes:
        r["origin_name"] = locations.get(r["origin_location_id"], f"#{r['origin_location_id']}")
        r["dest_name"] = locations.get(r["dest_location_id"], f"#{r['dest_location_id']}")

    # --- NEW: support map + form context (mirrors your index route) ---
    start_query = request.args.get("start", "") or ""
    end_query   = request.args.get("end", "") or ""

    start_lng = request.args.get("start_lng")
    start_lat = request.args.get("start_lat")
    end_lng   = request.args.get("end_lng")
    end_lat   = request.args.get("end_lat")

    start = None
    end = None
    if start_lng and start_lat:
        start = {"lon": float(start_lng), "lat": float(start_lat), "label": start_query}
    if end_lng and end_lat:
        end = {"lon": float(end_lng), "lat": float(end_lat), "label": end_query}

    return render_template(
        "routes_list.html",
        routes=routes,
        mapbox_token=MAPBOX_TOKEN,  # comes from your merged app.py
        start_query=start_query,
        end_query=end_query,
        start=start,
        end=end
    )

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
