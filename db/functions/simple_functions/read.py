from ..connect import get_db
import re

"""
Simple read functions that return entries from the database.
Supports filtering by columns, limits, and specific IDs.
"""


def _cols_arg(columns):
    """
    Takes a list of column names and returns a comma separated string.
    :param columns: list of column names
    """
    if columns is None:
        return None
    if not isinstance(columns, (list, tuple)):
        raise ValueError("columns must be a list or None")

    # Security: Validate column names to prevent SQL injection
    # Allow alphanumeric and underscores
    valid_col_pattern = re.compile(r"^[a-zA-Z0-9_]+$")
    for col in columns:
        if not valid_col_pattern.match(col):
            raise ValueError(f"Invalid column name: {col}")

    return ", ".join(columns) if columns else None


def _limit_arg(limit):
    """
    Converts strings to ints and checks if value is positive.
    :param limit: string or int representing number of rows to return
    """
    if limit is None:
        return None
    n = int(limit)
    return n if n > 0 else None


def _ids_arg(ids):
    """
    Takes a list of IDs and turns them into a comma separated string.
    :param ids: list of requested IDs
    """
    if ids is None:
        return None

    if not isinstance(ids, (list, tuple)):
        ids = [ids]

    if not ids:
        return None

    # Quote strings, leave numbers as is
    formatted = []
    for i in ids:
        if isinstance(i, str):
            # Security: Escape backslashes first to prevent escaping the closing quote
            val = i.replace("\\", "\\\\").replace("'", "''")
            formatted.append(f"'{val}'")
        else:
            formatted.append(str(i))
    return ",".join(formatted)


def _call_view_proc(proc_name, tenant_id, conn=None, columns=None, limit=None, ids=None):
    """
    Helper to format proc calls then request data from MySQL.
    :param proc_name: name of procedure
    :param columns: list of columns to return or none
    :param limit: number of records to return or none
    :param ids: list of ids or none
    """
    should_close = False
    if conn is None:
        conn = get_db()
        should_close = True
    
    if conn is None:
        raise RuntimeError("Failed to connect to database")

    try:
        cur = conn.cursor(dictionary=True)

        cur.callproc(proc_name, [
            tenant_id,
            _cols_arg(columns),
            _limit_arg(limit),
            _ids_arg(ids),
        ])

        rows = []
        for r in cur.stored_results():
            rows.extend(r.fetchall())

        cur.close()
        return rows
    finally:
        if should_close and conn:
            conn.close()


def view_locations(tenant_id, conn=None, columns=None, limit=None, ids=None):
    return _call_view_proc("view_locations", tenant_id, conn, columns, limit, ids)


def view_products_master(tenant_id, conn=None, columns=None, limit=None, ids=None):
    return _call_view_proc("view_products_master", tenant_id, conn, columns, limit, ids)


def view_drivers(tenant_id, conn=None, columns=None, limit=None, ids=None):
    return _call_view_proc("view_drivers", tenant_id, conn, columns, limit, ids)


def view_vehicles(tenant_id, conn=None, columns=None, limit=None, ids=None):
    return _call_view_proc("view_vehicles", tenant_id, conn, columns, limit, ids)


def view_entities(tenant_id, conn=None, columns=None, limit=None, ids=None):
    return _call_view_proc("view_entities", tenant_id, conn, columns, limit, ids)


def view_supply(tenant_id, conn=None, columns=None, limit=None, ids=None):
    return _call_view_proc("view_supply", tenant_id, conn, columns, limit, ids)


def view_demand(tenant_id, conn=None, columns=None, limit=None, ids=None):
    return _call_view_proc("view_demand", tenant_id, conn, columns, limit, ids)


def view_routes(tenant_id, conn=None, columns=None, limit=None, ids=None):
    return _call_view_proc("view_routes", tenant_id, conn, columns, limit, ids)


def view_scenarios(tenant_id, conn=None, columns=None, limit=None, ids=None):
    return _call_view_proc("view_scenarios", tenant_id, conn, columns, limit, ids)


def view_manifest_items(tenant_id, conn=None, columns=None, limit=None, ids=None):
    return _call_view_proc("view_manifest_items", tenant_id, conn, columns, limit, ids)