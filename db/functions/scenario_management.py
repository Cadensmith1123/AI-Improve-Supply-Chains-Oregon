from db.functions.connect import get_db
from db.functions.simple_functions import read, create, delete
from decimal import Decimal #used to combat floating point errors
import pandas as pd
from datetime import date


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
        conn = None
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

    if current_gas_price is None:
        current_gas_price = 0.0


    if run_date in ("", None):
        run_date = date.today()

    if conn is None:
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
    conn=None
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

    if conn is None:
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
        unit_volume = None,
        price_per_item = None,
        conn = None
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
        raise ValueError("item_name is required")
    if cost_per_item is None or cost_per_item == "":
        cost_per_item = 0.0
    if items_per_unit is None or items_per_unit == "":
        items_per_unit = 1
    if unit_weight is None or unit_weight == "":
        unit_weight = 0.0
    if unit_volume is None or unit_volume == "":
        unit_volume = 0.0
    if price_per_item is None or price_per_item == "":
        price_per_item = 0.0
    


    def _to_int(x):
        return int(x) if x not in (None, "") else None

    def _to_dec(x):
        return Decimal(str(x)) if x not in (None, "") else None

    args = [
        int(scenario_id),
        _to_int(supply_id),
        _to_int(demand_id),
        str(item_name),
        _to_dec(quantity_loaded),
        _to_dec(cost_per_item),
        _to_int(items_per_unit),
        _to_dec(unit_weight),
        _to_dec(unit_volume),
        _to_dec(price_per_item),
    ]

    if conn is None:
        conn = get_db()
    cur = conn.cursor()

    cur.callproc("add_manifest_item", args)

    for r in cur.stored_results():
        new_id = r.fetchone()[0]

    conn.commit()
    cur.close()

    return new_id


def get_trip_details(scenario_id, conn=None):
    if scenario_id in (None, ""):
        raise ValueError("scenario_id is required")
    scenario_id = int(scenario_id)

    if conn is None:
        conn = get_db()
    cur = conn.cursor(dictionary=True)

    cur.callproc("get_trip_details", [scenario_id])

    result_sets = [r.fetchall() for r in cur.stored_results()]
    cur.close()

    if not result_sets or not result_sets[0]:
        return None

    rows = result_sets[0]
    totals = result_sets[1][0] if len(result_sets) > 1 and result_sets[1] else {}

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
        "daily_maintenance_cost",
        "entered_revenue",
        "plan_load_min",
        "plan_unload_min",
    ]

    first = rows[0]
    header = {k: first.get(k) for k in header_cols}

    item_cols = [
        "product_name",
        "quantity_loaded",
        "items_per_unit",
        "unit_weight_lbs",
        "unit_volume",
        "cost_per_item",
        "price_per_item",
        "total_line_weight_lbs",
        "total_line_volume",
        "total_line_cogs",
        "total_line_revenue",
    ]

    items = []
    for row in rows:
        if row.get("product_name") is None and row.get("quantity_loaded") is None:
            continue
        items.append({k: row.get(k) for k in item_cols})

    return {"header": header, "items": items, "totals": totals}


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


# def export_trip_csv(scenario_id, path):
#     trip_details = get_trip_details(scenario_id)
#     if trip_details is None:
#         raise ValueError("Scenario not found")

#     df = trip_details_to_dataframe(trip_details)

#     df.to_csv(path, index=False)


def build_trip_costs_row(trip_details, drive_minutes_est=60, fuel_cost_est=0.0):
    header = trip_details["header"]
    items = trip_details["items"]
    totals = trip_details.get("totals") or {}

    # Snapshot inputs
    drive_rate = float(header.get("driver_drive_rate") or 0)
    load_rate = float(header.get("driver_load_rate") or 0)
    daily_ins = float(header.get("daily_insurance") or 0)
    daily_maintenance_cost = float(header.get("daily_maintenance_cost") or 0)

    load_min = float(header.get("plan_load_min") or 0)
    unload_min = float(header.get("plan_unload_min") or 0)
    drive_min = float(drive_minutes_est)

    # Labor costs
    driver_drive_cost = (drive_min / 60) * drive_rate
    driver_load_cost = (load_min / 60) * load_rate
    driver_unload_cost = (unload_min / 60) * load_rate
    driver_total_cost = driver_drive_cost + driver_load_cost + driver_unload_cost

    # Prefer proc totals (more robust), but fall back to summing items
    total_cogs = float(totals.get("total_cogs") or sum(float(x.get("total_line_cogs") or 0) for x in items))
    total_weight = float(totals.get("total_weight_lbs") or sum(float(x.get("total_line_weight_lbs") or 0) for x in items))
    total_volume = float(totals.get("total_volume") or sum(float(x.get("total_line_volume") or 0) for x in items))

    entered_revenue = float(totals.get("entered_revenue") or header.get("entered_revenue") or 0)
    calculated_revenue = float(totals.get("calculated_revenue") or sum(float(x.get("total_line_revenue") or 0) for x in items))

    total_cost_est = total_cogs + driver_total_cost + daily_ins + daily_maintenance_cost + float(fuel_cost_est)

    profit_vs_entered = entered_revenue - total_cost_est
    profit_vs_calculated = calculated_revenue - total_cost_est

    return {
        "scenario_id": header.get("scenario_id"),
        "run_date": header.get("run_date"),
        "route_name": header.get("route_name"),
        "vehicle_name": header.get("vehicle_name"),
        "driver_name": header.get("driver_name"),

        "drive_minutes_est": drive_min,
        "load_minutes_plan": load_min,
        "unload_minutes_plan": unload_min,

        "driver_drive_rate_per_hr": drive_rate,
        "driver_load_rate_per_hr": load_rate,

        "daily_insurance": daily_ins,
        "daily_maintenance_cost": daily_maintenance_cost,
        "fuel_cost_est": round(float(fuel_cost_est), 2),

        "driver_drive_cost_est": round(driver_drive_cost, 2),
        "driver_load_cost_est": round(driver_load_cost, 2),
        "driver_unload_cost_est": round(driver_unload_cost, 2),
        "driver_cost_total_est": round(driver_total_cost, 2),

        "line_item_count": int(totals.get("line_item_count") or len(items)),
        "total_weight_lbs": round(total_weight, 2),
        "total_volume": round(total_volume, 2),

        "total_cogs": round(total_cogs, 2),
        "entered_revenue": round(entered_revenue, 2),
        "calculated_revenue": round(calculated_revenue, 2),

        "profit_est_entered": round(profit_vs_entered, 2),
        "profit_est_calculated": round(profit_vs_calculated, 2),

        "margin_est_entered": round((profit_vs_entered / entered_revenue) if entered_revenue else 0, 4),
        "margin_est_calculated": round((profit_vs_calculated / calculated_revenue) if calculated_revenue else 0, 4),
    }


def export_trip_csv(trip_details, path):
    """
    Writes a two-section CSV using pre-fetched trip_details:
      - TRIP_COSTS (one row)
      - LINE_ITEMS (per-product rows)
    """
    if not trip_details:
        raise ValueError("No trip details provided")
    
    # Build cost DF
    costs_row = build_trip_costs_row(trip_details)
    costs_df = pd.DataFrame([costs_row])

    # Build line item DF
    items_df = pd.DataFrame(trip_details["items"])

    item_cols = [
        "product_name",
        "quantity_loaded",
        "items_per_unit",
        "unit_weight_lbs",
        "unit_volume",
        "cost_per_item",
        "price_per_item",
        "total_line_weight_lbs",
        "total_line_volume",
        "total_line_cogs",
        "total_line_revenue",
    ]
    if not items_df.empty:
        items_df = items_df[[c for c in item_cols if c in items_df.columns]]

        with open(path, "w", newline="", encoding="utf-8") as f:
            f.write("TRIP_COSTS\n")
            costs_df.to_csv(f, index=False)

            f.write("\n")
            f.write("LINE_ITEMS\n")
            items_df.to_csv(f, index=False)