from db.functions.connect import get_db
from db.functions.simple_functions import read, create
from decimal import Decimal, ROUND_HALF_UP  # keep Decimal for DB and currency correctness
import pandas as pd
from datetime import date

from frontend_flask.depreciation_insurance import (
    depreciation_cost_per_mile,
    insurance_cost_per_mile,
)


USEFUL_LIFE_YEARS = 8.0  # Policy: total projected mileage is based on 8 years of use, can be adjusted as needed

def get_locations(tenant_id, conn=None):
    location_data = read.view_locations(tenant_id, conn=conn, columns=['location_id', 'name'])
    return location_data


def _to_int(x):
    return int(x) if x not in (None, "") else None


def _to_dec(x):
    return Decimal(str(x)) if x not in (None, "") else None


def _to_float_strict(x) -> float:
    try:
        return float(x)
    except (TypeError, ValueError):
        return 0.0


def _safe_dec(val, default="0"):
    return Decimal(str(val)) if val is not None else Decimal(default)

def calculate_depreciation(purchase_price, salvage_value, yearly_mileage) -> Decimal:
    ym = _to_float_strict(yearly_mileage)
    total_projected_mileage = ym * USEFUL_LIFE_YEARS if ym > 0 else 0.0

    dppm = depreciation_cost_per_mile(
        purchase_price=purchase_price,
        salvage_value=salvage_value,
        total_projected_mileage=total_projected_mileage,
    )

    return Decimal(str(dppm)).quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)

def create_scenario(
        tenant_id,
        route_id,
        total_revenue,
        vehicle_id=None,
        driver_id=None,
        run_date=None,
        current_gas_price=None,
        conn=None
        ):

    if route_id is None:
        raise ValueError("route_id is required")
    if total_revenue is None:
        raise ValueError("total_revenue is required")

    route_id = int(route_id)
    vehicle_id = _to_int(vehicle_id)
    driver_id = _to_int(driver_id)
    total_revenue = _to_dec(total_revenue)
    current_gas_price = _to_dec(current_gas_price)

    if current_gas_price is None:
        current_gas_price = Decimal("0.0")

    if run_date in ("", None):
        run_date = date.today()

    depreciation = Decimal("0.0")
    if vehicle_id:
        v_rows = read.view_vehicles(tenant_id, conn=conn, ids=vehicle_id)
        if v_rows:
            v = v_rows[0]
            depreciation = calculate_depreciation(
                v.get('vehicle_purchase_price'),
                v.get('vehicle_estimated_salvage_value'),
                v.get('vehicle_estimated_yearly_milage')  
            )

    should_close = False
    if conn is None:
        conn = get_db()
        should_close = True

    if conn is None:
        raise RuntimeError("Failed to connect to database")

    try:
        cur = conn.cursor()

        args = [
            tenant_id,
            route_id,
            vehicle_id,
            driver_id,
            run_date,
            current_gas_price,
            total_revenue,
            depreciation,  
            0
        ]
        result = cur.callproc("create_trip_header", args)
        conn.commit()
        cur.close()
    finally:
        if should_close and conn:
            conn.close()

    new_scenario_id = result[-1]

    return new_scenario_id


def update_scenario(
    tenant_id,
    scenario_id,
    route_id=None,
    total_revenue=None,
    vehicle_id=None,
    driver_id=None,
    run_date=None,
    current_gas_price=None,
    conn=None
):

    should_close = False
    if conn is None:
        conn = get_db()
        should_close = True

    if conn is None:
        raise RuntimeError("Failed to connect to database")

    depreciation = None
    if vehicle_id is not None:
        v_rows = read.view_vehicles(tenant_id, conn=conn, ids=vehicle_id)
        if v_rows:
            v = v_rows[0]
            depreciation = calculate_depreciation(
                v.get('vehicle_purchase_price'),
                v.get('vehicle_estimated_salvage_value'),
                v.get('vehicle_estimated_yearly_milage') 
            )

    try:
        cur = conn.cursor(dictionary=True)

        args = [
            tenant_id,
            int(scenario_id),
            _to_int(route_id),
            _to_int(vehicle_id),
            _to_int(driver_id),
            run_date if run_date not in (None, "") else None,
            _to_dec(current_gas_price),
            _to_dec(total_revenue),
            depreciation
        ]

        cur.callproc("update_trip_header", args)

        rows = []
        for r in cur.stored_results():
            rows.extend(r.fetchall())
        conn.commit()
        cur.close()
        return rows[0] if rows else None
    finally:
        if should_close and conn:
            conn.close()


def refresh_scenario(tenant_id, scenario_id, conn=None):

    should_close = False
    if conn is None:
        conn = get_db()
        should_close = True

    if conn is None:
        raise RuntimeError("Failed to connect to database")

    try:
        scenarios = read.view_scenarios(tenant_id, ids=scenario_id, conn=conn)
        if not scenarios:
            return False

        scenario = scenarios[0]
        vehicle_id = scenario.get('vehicle_id')

        depreciation = Decimal("0.000")
        if vehicle_id:
            v_rows = read.view_vehicles(tenant_id, ids=vehicle_id, conn=conn)
            if v_rows:
                v = v_rows[0]
                depreciation = calculate_depreciation(
                    v.get('vehicle_purchase_price'),
                    v.get('vehicle_estimated_salvage_value'),
                    v.get('vehicle_estimated_yearly_milage') 
                )

        cur = conn.cursor()
        cur.callproc("refresh_trip_snapshots", [tenant_id, scenario_id, depreciation])
        conn.commit()
        cur.close()
        return True
    finally:
        if should_close and conn:
            conn.close()

def add_manifest_items(
        tenant_id,
        scenario_id,
        item_name,
        quantity_loaded,
        supply_id=None,
        demand_id=None,
        cost_per_item=None,
        items_per_unit=None,
        unit_weight_lbs=None,
        unit_volume=None,
        price_per_item=None,
        conn=None
):

    return create.add_manifest_item(
        tenant_id=tenant_id,
        scenario_id=scenario_id,
        item_name=item_name,
        quantity_loaded=quantity_loaded,
        supply_id=supply_id,
        demand_id=demand_id,
        snapshot_cost_per_item=cost_per_item,
        snapshot_items_per_unit=items_per_unit,
        snapshot_unit_weight=unit_weight_lbs,
        snapshot_unit_volume=unit_volume,
        snapshot_price_per_item=price_per_item,
        conn=conn
    )


def _calculate_line_metrics(row):
    """
    Pure function: Calculates extended totals (weight, volume, COGS, revenue) 
    for a single line item row. Handles key variations (input vs db).
    """
    qty = _safe_dec(row.get("quantity_loaded"))
    items_per_unit = _safe_dec(row.get("items_per_unit"), "1")
    unit_weight = _safe_dec(row.get("unit_weight_lbs"))
    unit_volume = _safe_dec(row.get("unit_volume"))
    cost = _safe_dec(row.get("cost_per_item"))
    price = _safe_dec(row.get("price_per_item"))

    return {
        "total_line_weight_lbs": qty * unit_weight,
        "total_line_volume": qty * unit_volume,
        "total_line_cogs": qty * items_per_unit * cost,
        "total_line_revenue": qty * items_per_unit * price
    }


def _aggregate_totals(items, entered_revenue):
    return {
        "line_item_count": len(items),
        "total_weight_lbs": sum((i["total_line_weight_lbs"] for i in items), Decimal(0)),
        "total_volume": sum((i["total_line_volume"] for i in items), Decimal(0)),
        "total_cogs": sum((i["total_line_cogs"] for i in items), Decimal(0)),
        "calculated_revenue": sum((i["total_line_revenue"] for i in items), Decimal(0)),
        "entered_revenue": _safe_dec(entered_revenue)
    }


def calculate_scenario_metrics(items, entered_revenue=0):
    processed_items = []
    for item in items:
        metrics = _calculate_line_metrics(item)
        processed_item = {**item, **metrics}
        processed_items.append(processed_item)

    totals = _aggregate_totals(processed_items, entered_revenue)
    return {"items": processed_items, "totals": totals}

def get_trip_details(tenant_id, scenario_id, conn=None):
    if scenario_id in (None, ""):
        raise ValueError("scenario_id is required")
    scenario_id = int(scenario_id)

    should_close = False
    if conn is None:
        conn = get_db()
        should_close = True

    if conn is None:
        raise RuntimeError("Failed to connect to database")

    try:
        cur = conn.cursor(dictionary=True)

        cur.callproc("get_trip_details", [tenant_id, scenario_id])

        result_sets = [r.fetchall() for r in cur.stored_results()]
        cur.close()
    finally:
        if should_close and conn:
            conn.close()

    if not result_sets or not result_sets[0]:
        return None

    rows = result_sets[0]

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
        "depreciation_per_mile",
        "daily_insurance",          
        "daily_maintenance_cost",
        "entered_revenue",
        "plan_load_min",
        "plan_unload_min",
    ]

    first = rows[0]
    header = {k: first.get(k) for k in header_cols}

    try:
        scenarios_for_vehicle = read.view_scenarios(tenant_id, ids=scenario_id)
        if scenarios_for_vehicle:
            vehicle_id = scenarios_for_vehicle[0].get('vehicle_id')
            if vehicle_id:
                vrows = read.view_vehicles(tenant_id, ids=vehicle_id)
                if vrows:
                    v = vrows[0]
                    annual_ins_cost = v.get('annual_insurance_cost')             
                    yearly_mileage = v.get('vehicle_estimated_yearly_milage')    
                    icpm = insurance_cost_per_mile(annual_ins_cost, yearly_mileage)
                    header["daily_insurance"] = icpm  
    except Exception:
        pass

    item_cols = [
        "product_name",
        "quantity_loaded",
        "items_per_unit",
        "unit_weight_lbs",
        "unit_volume",
        "cost_per_item",
        "price_per_item",
    ]

    items = []
    for row in rows:
        if row.get("product_name") is None and row.get("quantity_loaded") is None:
            continue

        item_data = {k: row.get(k) for k in item_cols if k in row}

        metrics = _calculate_line_metrics(row)
        item_data.update(metrics)

        items.append(item_data)

    totals = _aggregate_totals(items, header.get("entered_revenue"))

    return {"header": header, "items": items, "totals": totals}


def build_trip_costs_row(trip_details, drive_minutes_est=60, fuel_cost_est=0.0, miles_est=50.0):
    header = trip_details["header"]
    items = trip_details["items"]
    totals = trip_details.get("totals") or {}

    # Snapshot inputs
    drive_rate = float(header.get("driver_drive_rate") or 0)
    load_rate = float(header.get("driver_load_rate") or 0)

    # Interpret "daily_insurance" header value as INSURANCE PER MILE (by design above)
    insurance_per_mile = float(header.get("daily_insurance") or 0.0)
    daily_maintenance_cost = float(header.get("daily_maintenance_cost") or 0)

    vehicle_mpg = float(header.get("vehicle_mpg") or 0)
    gas_price = float(header.get("gas_price") or 0)

    load_min = float(header.get("plan_load_min") or 0)
    unload_min = float(header.get("plan_unload_min") or 0)
    drive_min = float(drive_minutes_est)

    # Labor costs
    driver_drive_cost = (drive_min / 60) * drive_rate
    driver_load_cost = (load_min / 60) * load_rate
    driver_unload_cost = (unload_min / 60) * load_rate
    driver_total_cost = driver_drive_cost + driver_load_cost + driver_unload_cost

    # Asset costs
    depreciation_rate = float(header.get("depreciation_per_mile") or 0)
    depreciation_cost = miles_est * depreciation_rate

    # Insurance cost 
    insurance_cost = insurance_per_mile * miles_est

    calculated_fuel_cost = 0.0
    if vehicle_mpg > 0:
        calculated_fuel_cost = (miles_est / vehicle_mpg) * gas_price
    final_fuel_cost = calculated_fuel_cost if fuel_cost_est == 0.0 else float(fuel_cost_est)

    total_cogs = float(totals.get("total_cogs") or sum(float(x.get("total_line_cogs") or 0) for x in items))
    total_weight = float(totals.get("total_weight_lbs") or sum(float(x.get("total_line_weight_lbs") or 0) for x in items))
    total_volume = float(totals.get("total_volume") or sum(float(x.get("total_line_volume") or 0) for x in items))

    entered_revenue = float(totals.get("entered_revenue") or header.get("entered_revenue") or 0)
    calculated_revenue = float(totals.get("calculated_revenue") or sum(float(x.get("total_line_revenue") or 0) for x in items))

    total_cost_est = (
        total_cogs
        + driver_total_cost
        + insurance_cost            
        + daily_maintenance_cost
        + final_fuel_cost
        + depreciation_cost
    )

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

        # Audit: expose both the per-mile rate and per-trip computed cost 
        "insurance_per_mile": round(insurance_per_mile, 3),  
        "daily_insurance": round(insurance_cost, 2),         

        "daily_maintenance_cost": daily_maintenance_cost,
        "depreciation_cost_est": round(depreciation_cost, 2),
        "fuel_cost_est": round(final_fuel_cost, 2),

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
        "total_distance_miles": round(miles_est, 1),
    }


def export_trip_csv(trip_details, output_handle):
    if not trip_details:
        raise ValueError("No trip details provided")

    costs_row = build_trip_costs_row(trip_details)
    costs_df = pd.DataFrame([costs_row])

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

        should_close = False
        if isinstance(output_handle, str):
            f = open(output_handle, "w", newline="", encoding="utf-8")
            should_close = True
        else:
            f = output_handle

        try:
            f.write("TRIP_COSTS\n")
            costs_df.to_csv(f, index=False)
            f.write("\n")
            f.write("LINE_ITEMS\n")
            items_df.to_csv(f, index=False)
        finally:
            if should_close:
                f.close()


def export_flattened_csv(trip_details_list, output_handle):
    if not trip_details_list:
        return

    all_rows = []
    for details in trip_details_list:
        header_metrics = build_trip_costs_row(details)
        items = details.get("items", [])

        if not items:
            all_rows.append(header_metrics)
        else:
            for item in items:
                row = header_metrics.copy()
                row.update(item)
                all_rows.append(row)

    df = pd.DataFrame(all_rows)

    should_close = False
    if isinstance(output_handle, str):
        f = open(output_handle, "w", newline="", encoding="utf-8")
        should_close = True
    else:
        f = output_handle

    try:
        df.to_csv(f, index=False)
    finally:
        if should_close:
            f.close()


def export_summary_csv(trip_details_list, output_handle):
    """
    Writes a summary CSV for a list of trip_details.
    Each row contains header metrics only (no line items).
    """
    if not trip_details_list:
        return

    all_rows = []
    for details in trip_details_list:
        header_metrics = build_trip_costs_row(details)
        all_rows.append(header_metrics)

    df = pd.DataFrame(all_rows)

    should_close = False
    if isinstance(output_handle, str):
        f = open(output_handle, "w", newline="", encoding="utf-8")
        should_close = True
    else:
        f = output_handle

    try:
        df.to_csv(f, index=False)
    finally:
        if should_close:
            f.close()