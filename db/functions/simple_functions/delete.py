from ..connect import get_db

def _id_arg(id_value):
    """
    takes an id and converts to int if possible otherwise 
    returns string as provided. 
    
    :param id_value: string or int id of record being deleted
    """
    if id_value in (None, ""):
        return None
    try:
        return int(id_value)
    except (TypeError, ValueError):
        return id_value


def _call_delete_proc(proc_name, id_value):
    """
    Helper to call a delete stored procedure.

    :param proc_name: name of delete procedure
    :param id_value: primary key value (int or str depending on table)
    :return: any rows returned by the proc 
    """
    arg = _id_arg(id_value)
    if arg is None:
        raise ValueError("id is required")

    conn = get_db()
    cur = conn.cursor(dictionary=True)

    cur.callproc(proc_name, [arg])

    rows = []
    for r in cur.stored_results():
        rows.extend(r.fetchall())

    conn.commit()
    cur.close()
    return rows


def delete_location(location_id):
    return _call_delete_proc("delete_location", location_id)


def delete_product_master(product_code):
    return _call_delete_proc("delete_product_master", product_code)


def delete_driver(driver_id):
    return _call_delete_proc("delete_driver", driver_id)


def delete_vehicle(vehicle_id):
    return _call_delete_proc("delete_vehicle", vehicle_id)


def delete_entity(entity_id):
    return _call_delete_proc("delete_entity", entity_id)


def delete_supply(supply_id):
    return _call_delete_proc("delete_supply", supply_id)


def delete_demand(demand_id):
    return _call_delete_proc("delete_demand", demand_id)


def delete_route(route_id):
    return _call_delete_proc("delete_route", route_id)


def delete_scenario(scenario_id):
    return _call_delete_proc("delete_scenario", scenario_id)


def delete_manifest_item(manifest_item_id):
    return _call_delete_proc("delete_manifest_item", manifest_item_id)


def delete_plan(scenario_id):

    return _call_delete_proc("delete_plan", scenario_id)