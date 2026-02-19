# map_route.py
import os
from flask import Blueprint, render_template, abort, jsonify
import access_db as db
from dotenv import load_dotenv
import os

load_dotenv()

map_bp = Blueprint("map", __name__, template_folder="templates")

def _get_mapbox_token_or_abort():
    token = os.getenv("MAPBOX_TOKEN")
    if not token:
        abort(500, description="MAPBOX_TOKEN is not set in the environment.")
    return token

@map_bp.get("/routes/<int:route_id>/map")
def route_map_embed(route_id: int):
    route = db.get_route(route_id)
    if not route:
        abort(404)

    start_address = route.get("origin_address")
    end_address   = route.get("dest_address")
    mapbox_token  = _get_mapbox_token_or_abort()

    return render_template(
        "map_view.html",   # or "map_embed.html" if that's your file
        start_address=start_address,
        end_address=end_address,
        mapbox_token=mapbox_token,
    )