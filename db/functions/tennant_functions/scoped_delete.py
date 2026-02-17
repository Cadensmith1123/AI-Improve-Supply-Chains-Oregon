from flask import g
from ..simple_functions.delete import (
    delete_location,
    delete_product_master,
    delete_driver,
    delete_vehicle,
    delete_entity,
    delete_supply,
    delete_demand,
    delete_route,
    delete_scenario,
    delete_manifest_item,
    delete_plan,
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


def delete_location_scoped(*, location_id, conn=None):
    return delete_location(_tenant_id(), location_id, conn=conn)


def delete_product_master_scoped(*, product_code, conn=None):
    return delete_product_master(_tenant_id(), product_code, conn=conn)


def delete_driver_scoped(*, driver_id, conn=None):
    return delete_driver(_tenant_id(), driver_id, conn=conn)


def delete_vehicle_scoped(*, vehicle_id, conn=None):
    return delete_vehicle(_tenant_id(), vehicle_id, conn=conn)


def delete_entity_scoped(*, entity_id, conn=None):
    return delete_entity(_tenant_id(), entity_id, conn=conn)


def delete_supply_scoped(*, supply_id, conn=None):
    return delete_supply(_tenant_id(), supply_id, conn=conn)


def delete_demand_scoped(*, demand_id, conn=None):
    return delete_demand(_tenant_id(), demand_id, conn=conn)


def delete_route_scoped(*, route_id, conn=None):
    return delete_route(_tenant_id(), route_id, conn=conn)


def delete_scenario_scoped(*, scenario_id, conn=None):
    return delete_scenario(_tenant_id(), scenario_id, conn=conn)


def delete_manifest_item_scoped(*, manifest_item_id, conn=None):
    return delete_manifest_item(_tenant_id(), manifest_item_id, conn=conn)


def delete_plan_scoped(*, scenario_id, conn=None):
    return delete_plan(_tenant_id(), scenario_id, conn=conn)