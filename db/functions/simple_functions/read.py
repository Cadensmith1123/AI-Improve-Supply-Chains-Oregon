from ..connect import get_db

"""simple read functions that return all entries from all columns with no 
arguments or allows for list of columns and number of entries. Also allows 
for a simple list  """


def _cols_arg(columns):
    """
    takes a list of column names and returns a 
    comma separated string

    :param columns: list of column names
    """
    if columns is None:
        return None
    if not isinstance(columns, (list, tuple)):
        raise ValueError("columns must be a list or None")
    return ", ".join(columns) if columns else None


def _limit_arg(limit):
    """
    Converts strings to ints and checks if value 
    is positive
    
    :param limit: string or int representing number of 
    rows to return
    """
    if limit is None:
        return None
    n = int(limit)
    return n if n > 0 else None


def _ids_arg(ids):
    """
    takes a list of id's and turns them into 
    a comma separated string.
    
    :param ids: list of requested IDs
    """
    if ids is None:
        return None

    if isinstance(ids, (list, tuple)):
        if not ids:
            return None
        return ",".join(str(i) for i in ids)

    return str(ids)


def _call_view_proc(proc_name, conn=get_db(), columns=None, limit=None, ids=None):
    """
    Helper to format proc calls then request data from MYSQL
    
    :param proc_name: name of procedure
    :param columns: list of columns to return or none
    :param limit: number of records to return or none
    :param ids: list of ids or none
    """
    cur = conn.cursor(dictionary=True)

    cur.callproc(proc_name, [
        _cols_arg(columns),
        _limit_arg(limit),
        _ids_arg(ids),
    ])

    rows = []
    for r in cur.stored_results():
        rows.extend(r.fetchall())

    cur.close()
    return rows


def view_locations(conn=get_db(), columns=None, limit=None, ids=None):
    return _call_view_proc("view_locations", conn, columns, limit, ids)


def view_products_master(conn=get_db(), columns=None, limit=None, ids=None):
    return _call_view_proc("view_products_master", conn, columns, limit, ids)


def view_drivers(conn=get_db(), columns=None, limit=None, ids=None):
    return _call_view_proc("view_drivers", conn, columns, limit, ids)


def view_vehicles(conn=get_db(), columns=None, limit=None, ids=None):
    return _call_view_proc("view_vehicles", conn, columns, limit, ids)


def view_entities(conn=get_db(), columns=None, limit=None, ids=None):
    return _call_view_proc("view_entities", conn, columns, limit, ids)


def view_supply(conn=get_db(), columns=None, limit=None, ids=None):
    return _call_view_proc("view_supply", conn, columns, limit, ids)


def view_demand(conn=get_db(), columns=None, limit=None, ids=None):
    return _call_view_proc("view_demand", conn, columns, limit, ids)


def view_routes(conn=get_db(), columns=None, limit=None, ids=None):
    return _call_view_proc("view_routes", conn, columns, limit, ids)


def view_scenarios(conn=get_db(), columns=None, limit=None, ids=None):
    return _call_view_proc("view_scenarios", conn, columns, limit, ids)


def view_manifest_items(conn=get_db(), columns=None, limit=None, ids=None):
    return _call_view_proc("view_manifest_items", conn, columns, limit, ids)