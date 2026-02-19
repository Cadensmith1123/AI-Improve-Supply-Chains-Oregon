from flask import g

from ..simple_functions.read import (
    view_locations,
    view_products_master,
    view_drivers,
    view_vehicles,
    view_entities,
    view_supply,
    view_demand,
    view_routes,
    view_scenarios,
    view_manifest_items,
)


def _tenant_id():
    """
    Fetch tenant_id from request context.
    Fail loudly if missing.
    """
    tid = getattr(g, "tenant_id", None)
    if tid is None:
        raise RuntimeError("Missing g.tenant_id (auth middleware not run?)")
    return int(tid)


def view_locations_scoped(*, conn=None, columns=None, limit=None, ids=None):
    return view_locations(
        _tenant_id(),
        conn=conn,
        columns=columns,
        limit=limit,
        ids=ids,
    )


def view_products_master_scoped(*, conn=None, columns=None, limit=None, ids=None):
    return view_products_master(
        _tenant_id(),
        conn=conn,
        columns=columns,
        limit=limit,
        ids=ids,
    )


def view_drivers_scoped(*, conn=None, columns=None, limit=None, ids=None):
    return view_drivers(
        _tenant_id(),
        conn=conn,
        columns=columns,
        limit=limit,
        ids=ids,
    )


def view_vehicles_scoped(*, conn=None, columns=None, limit=None, ids=None):
    return view_vehicles(
        _tenant_id(),
        conn=conn,
        columns=columns,
        limit=limit,
        ids=ids,
    )


def view_entities_scoped(*, conn=None, columns=None, limit=None, ids=None):
    return view_entities(
        _tenant_id(),
        conn=conn,
        columns=columns,
        limit=limit,
        ids=ids,
    )


def view_supply_scoped(*, conn=None, columns=None, limit=None, ids=None):
    return view_supply(
        _tenant_id(),
        conn=conn,
        columns=columns,
        limit=limit,
        ids=ids,
    )


def view_demand_scoped(*, conn=None, columns=None, limit=None, ids=None):
    return view_demand(
        _tenant_id(),
        conn=conn,
        columns=columns,
        limit=limit,
        ids=ids,
    )


def view_routes_scoped(*, conn=None, columns=None, limit=None, ids=None):
    return view_routes(
        _tenant_id(),
        conn=conn,
        columns=columns,
        limit=limit,
        ids=ids,
    )


def view_scenarios_scoped(*, conn=None, columns=None, limit=None, ids=None):
    return view_scenarios(
        _tenant_id(),
        conn=conn,
        columns=columns,
        limit=limit,
        ids=ids,
    )


def view_manifest_items_scoped(*, conn=None, columns=None, limit=None, ids=None):
    return view_manifest_items(
        _tenant_id(),
        conn=conn,
        columns=columns,
        limit=limit,
        ids=ids,
    )