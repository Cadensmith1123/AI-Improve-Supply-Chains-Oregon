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


def _call_delete_proc(proc_name, tenant_id, id_value, conn=None):
    """
    Helper to call a delete stored procedure.

    :param proc_name: name of delete procedure
    :param id_value: primary key value (int or str depending on table)
    :return: any rows returned by the proc 
    """
    arg = _id_arg(id_value)
    if arg is None:
        raise ValueError("id is required")

    should_close = False
    if conn is None:
        conn = get_db()
        should_close = True
    
    if conn is None:
        raise RuntimeError("Failed to connect to database")
    
    try:
        cur = conn.cursor(dictionary=True)

        cur.callproc(proc_name, [tenant_id, arg])

        rows = []
        for r in cur.stored_results():
            rows.extend(r.fetchall())

        conn.commit()
        cur.close()
        return rows
    finally:
        if should_close and conn:
            conn.close()


def delete_location(tenant_id, location_id, conn=None):
    return _call_delete_proc("delete_location", tenant_id, location_id, conn=conn)


def delete_product_master(tenant_id, product_code, conn=None):
    return _call_delete_proc("delete_product_master", tenant_id, product_code, conn=conn)


def delete_driver(tenant_id, driver_id, conn=None):
    return _call_delete_proc("delete_driver", tenant_id, driver_id, conn=conn)


def delete_vehicle(tenant_id, vehicle_id, conn=None):
    return _call_delete_proc("delete_vehicle", tenant_id, vehicle_id, conn=conn)


def delete_entity(tenant_id, entity_id, conn=None):
    return _call_delete_proc("delete_entity", tenant_id, entity_id, conn=conn)


def delete_supply(tenant_id, supply_id, conn=None):
    return _call_delete_proc("delete_supply", tenant_id, supply_id, conn=conn)


def delete_demand(tenant_id, demand_id, conn=None):
    return _call_delete_proc("delete_demand", tenant_id, demand_id, conn=conn)


def delete_route(tenant_id, route_id, conn=None):
    return _call_delete_proc("delete_route", tenant_id, route_id, conn=conn)


def delete_scenario(tenant_id, scenario_id, conn=None):
    return _call_delete_proc("delete_scenario", tenant_id, scenario_id, conn=conn)


def delete_manifest_item(tenant_id, manifest_item_id, conn=None):
    return _call_delete_proc("delete_manifest_item", tenant_id, manifest_item_id, conn=conn)


def delete_plan(tenant_id, scenario_id, conn=None):
    return _call_delete_proc("delete_plan", tenant_id, scenario_id, conn=conn)