# db.py
# Mock data now. Later teammate replaces these with stored procedure calls.

_LOCATIONS = [
    {"location_id": 1, "name": "Portland Hub"},
    {"location_id": 2, "name": "Seattle DC"},
    {"location_id": 3, "name": "Salem Store"},
]

# sales_amount is now PER ROUTE
_ROUTES = [
    {"route_id": 101, "name": "PDX → SEA", "origin_location_id": 1, "dest_location_id": 2, "sales_amount": 1200.50},
    {"route_id": 102, "name": "SEA → SLM", "origin_location_id": 2, "dest_location_id": 3, "sales_amount": 950.00},
]

def list_routes():
    return _ROUTES

def list_locations():
    return _LOCATIONS

def get_route(route_id: int):
    for r in _ROUTES:
        if r["route_id"] == route_id:
            return r
    return None

def update_route(route_id: int, name: str, origin_location_id: int, dest_location_id: int, sales_amount: float):
    route = get_route(route_id)
    if not route:
        return False, "NOT_FOUND"

    # simple FK check
    loc_ids = {l["location_id"] for l in _LOCATIONS}
    if origin_location_id not in loc_ids or dest_location_id not in loc_ids:
        return False, "FK_ERROR"

    route["name"] = name
    route["origin_location_id"] = origin_location_id
    route["dest_location_id"] = dest_location_id
    route["sales_amount"] = sales_amount
    return True, None
