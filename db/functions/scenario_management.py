from .connect import get_db
from .simple_functions import read, create, delete
from decimal import Decimal #used to combat floating point errors
import pandas as pd


def get_locations():
    location_data = read.view_locations(columns=['location_id', 'name'])
    return location_data


def create_scenario(
        route_id,
        total_revenue,
        vehicle_id = None,
        driver_id = None,
        run_date = None,
        current_gas_price = None,
        ):
    """
    Creates new scenario header can take string int or float as inputs. 
    
    :param route_id: route ID (required)
    :param total_revenue: total revenue (required)
    :param vehicle_id: vehicle id (optional)
    :param driver_id: driver id (optional)
    :param run_date: run date (optional defaults to current date)
    :param current_gas_price: gas price (optional)

    Returns the ID of the newly created scenario. 
    """
    if route_id is None:
        raise ValueError("route_id is required")
    if total_revenue is None:
        raise ValueError("total_revenue is required")

    def _to_int(x):
        return int(x) if x not in (None, "") else None

    def _to_dec(x):
        return Decimal(str(x)) if x not in (None, "") else None

    route_id = int(route_id)
    vehicle_id = _to_int(vehicle_id)
    driver_id = _to_int(driver_id)
    total_revenue = _to_dec(total_revenue)
    current_gas_price = _to_dec(current_gas_price)

    if run_date in ("", None):
        run_date = None

    conn = get_db()
    cur = conn.cursor()

    args = [
        route_id,
        vehicle_id,
        driver_id,
        run_date,
        current_gas_price,
        total_revenue,
        0
    ]
    result = cur.callproc("create_trip_header", args)
    conn.commit()
    cur.close()

    new_scenario_id = result[-1]

    return new_scenario_id


def update_scenario(
    scenario_id,
    route_id=None,
    total_revenue=None,
    vehicle_id=None,
    driver_id=None,
    run_date=None,
    current_gas_price=None,
):
    """
    Docstring for update_scenario
    
    :param scenario_id: Scenario id (required)
    :param route_id: Route id (optional)
    :param total_revenue: total_revenue (optional)
    :param vehicle_id: vehicle id (optional)
    :param driver_id: driver id (optional)
    :param run_date: run date (optional)
    :param current_gas_price: gas price (optional)
    """
    def _to_int(x):
        return int(x) if x not in (None, "") else None

    def _to_dec(x):
        return Decimal(str(x)) if x not in (None, "") else None

    conn = get_db()
    cur = conn.cursor(dictionary=True)

    args = [
        int(scenario_id),
        _to_int(route_id),
        _to_int(vehicle_id),
        _to_int(driver_id),
        run_date if run_date not in (None, "") else None,
        _to_dec(current_gas_price),
        _to_dec(total_revenue),
    ]

    cur.callproc("update_trip_header", args)

    rows = []
    for r in cur.stored_results():
        rows.extend(r.fetchall())

    conn.commit()
    cur.close()
    return rows[0] if rows else None


def add_manifest_items(
        scenario_id,
        item_name,
        quantity_loaded,
        supply_id = None,
        demand_id = None,
        cost_per_item = None,
        items_per_unit = None,
        unit_weight = None,
        price_per_item = None
):
    """
    adds a product to the trip manifest
    
    :param scenario_id: scenario id (required)
    :param item_name: name of item (required)
    :param quantity_loaded: quantity loaded (handling units, required)
    :param supply_id: supply id (optional)
    :param demand_id: demand id (optional)
    :param cost_per_item: cost per item (optional)
    :param items_per_unit: items per handling unit (optional)
    :param unit_weight: weight per handling unit (optional)
    :param price_per_item: sale price per item (optional)
    """
    if scenario_id is None or scenario_id == "":
        raise ValueError("scenario_id is required")
    if quantity_loaded is None or quantity_loaded == "":
        raise ValueError("quantity_loaded is required")
    if item_name is None or item_name == "":
        raise ValueError("quantity_loaded is required")

    def _to_int(x):
        return int(x) if x not in (None, "") else None

    def _to_dec(x):
        return Decimal(str(x)) if x not in (None, "") else None

    args = [
        int(scenario_id),
        _to_int(supply_id),
        _to_int(demand_id),
        item_name,
        _to_dec(quantity_loaded),
        _to_dec(cost_per_item),
        _to_int(items_per_unit),
        _to_dec(unit_weight),
        _to_dec(price_per_item),
    ]

    conn = get_db()
    cur = conn.cursor()

    cur.callproc("create_manifest_item", args)

    conn.commit()
    cur.close()



def get_trip_details(scenario_id):
    """
    Returns trip header + manifest line items for a scenario.

    :param scenario_id: scenario id (required)
    :return: dict with keys:
        - "header": dict (scenario-level fields)
        - "items": list[dict] (manifest rows)
    """
    if scenario_id in (None, ""):
        raise ValueError("scenario_id is required")

    scenario_id = int(scenario_id)

    conn = get_db()
    cur = conn.cursor(dictionary=True)

    cur.callproc("get_trip_details", [scenario_id])

    rows = []
    for r in cur.stored_results():
        rows.extend(r.fetchall())

    cur.close()

    if not rows:
        return None

    header_cols = [
        "scenario_id",
        "run_date",
        "route_name",
        "vehicle_name",
        "driver_name",
        "driver_drive_rate",
        "driver_load_rate",
        "vehicle_mpg",
        "gas_price",
        "daily_insurance",
        "plan_load_min",
        "plan_unload_min",
    ]

    first = rows[0]
    header = {k: first.get(k) for k in header_cols}

    item_cols = [
        "product_name",
        "quantity_loaded",
        "unit_weight_lbs",
        "items_per_unit",
        "cost_per_item",
        "price_per_item",
        "total_line_weight_lbs",
        "total_line_cogs",
        "total_line_revenue",
    ]

    items = []
    for row in rows:
        if row.get("product_name") is None and row.get("quantity_loaded") is None:
            continue
        items.append({k: row.get(k) for k in item_cols})

    return {
        "header": header,
        "items": items,
    }

    
def trip_details_to_dataframe(trip_details):
    """
    Converts get_trip_details() output to a flat DataFrame.
    Each manifest item becomes one row with repeated header fields.
    """
    header = trip_details["header"]
    items = trip_details["items"]

    if not items:
        return pd.DataFrame([header])

    rows = []
    for item in items:
        row = {}
        row.update(header)
        row.update(item)
        rows.append(row)

    return pd.DataFrame(rows)

def export_trip_csv(scenario_id, path):
    trip_details = get_trip_details(scenario_id)
    if trip_details is None:
        raise ValueError("Scenario not found")

    df = trip_details_to_dataframe(trip_details)

    df.to_csv(path, index=False)
