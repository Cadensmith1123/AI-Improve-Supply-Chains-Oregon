from connect import get_db

"""simple read functions that return all entries from all columns with no 
arguments or allows for list of columns and number of entries to requested"""


def _cols_arg(columns):
    if columns is None:
        return None
    if not isinstance(columns, (list, tuple)):
        raise ValueError("columns must be a list or None")
    return ", ".join(columns) if columns else None


def _limit_arg(limit):
    if limit is None:
        return None
    n = int(limit)
    return n if n > 0 else None


def view_locations(columns=None, limit=None):
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    cur.callproc("view_locations", [_cols_arg(columns), _limit_arg(limit)])
    rows = []
    for r in cur.stored_results():
        rows.extend(r.fetchall())
    cur.close()
    return rows


def view_products_master(columns=None, limit=None):
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    cur.callproc("view_products_master", [_cols_arg(columns), _limit_arg(limit)])
    rows = []
    for r in cur.stored_results():
        rows.extend(r.fetchall())
    cur.close()
    return rows


def view_drivers(columns=None, limit=None):
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    cur.callproc("view_drivers", [_cols_arg(columns), _limit_arg(limit)])
    rows = []
    for r in cur.stored_results():
        rows.extend(r.fetchall())
    cur.close()
    return rows


def view_vehicles(columns=None, limit=None):
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    cur.callproc("view_vehicles", [_cols_arg(columns), _limit_arg(limit)])
    rows = []
    for r in cur.stored_results():
        rows.extend(r.fetchall())
    cur.close()
    return rows


def view_entities(columns=None, limit=None):
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    cur.callproc("view_entities", [_cols_arg(columns), _limit_arg(limit)])
    rows = []
    for r in cur.stored_results():
        rows.extend(r.fetchall())
    cur.close()
    return rows


def view_supply(columns=None, limit=None):
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    cur.callproc("view_supply", [_cols_arg(columns), _limit_arg(limit)])
    rows = []
    for r in cur.stored_results():
        rows.extend(r.fetchall())
    cur.close()
    return rows


def view_demand(columns=None, limit=None):
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    cur.callproc("view_demand", [_cols_arg(columns), _limit_arg(limit)])
    rows = []
    for r in cur.stored_results():
        rows.extend(r.fetchall())
    cur.close()
    return rows


def view_routes(columns=None, limit=None):
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    cur.callproc("view_routes", [_cols_arg(columns), _limit_arg(limit)])
    rows = []
    for r in cur.stored_results():
        rows.extend(r.fetchall())
    cur.close()
    return rows


def view_scenarios(columns=None, limit=None):
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    cur.callproc("view_scenarios", [_cols_arg(columns), _limit_arg(limit)])
    rows = []
    for r in cur.stored_results():
        rows.extend(r.fetchall())
    cur.close()
    return rows


def view_manifest_items(columns=None, limit=None):
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    cur.callproc("view_manifest_items", [_cols_arg(columns), _limit_arg(limit)])
    rows = []
    for r in cur.stored_results():
        rows.extend(r.fetchall())
    cur.close()
    return rows
