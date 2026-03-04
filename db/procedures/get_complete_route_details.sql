DELIMITER $$

DROP PROCEDURE IF EXISTS get_complete_route_details $$

CREATE PROCEDURE get_complete_route_details(
    IN p_tenant_id INT,
    IN p_scenario_id INT
)
BEGIN
    -- 1. Header Details (Joined with Route, Locations, Vehicle, Driver)
    SELECT 
        s.scenario_id,
        s.run_date,
        s.snapshot_total_revenue as entered_revenue,
        s.snapshot_driver_wage as driver_drive_rate,
        s.snapshot_driver_load_wage as driver_load_rate,
        s.snapshot_vehicle_mpg as vehicle_mpg,
        s.snapshot_gas_price as gas_price,
        s.snapshot_depreciation_per_mile as depreciation_per_mile,
        s.snapshot_daily_insurance as daily_insurance,
        s.snapshot_daily_maintenance_cost as daily_maintenance_cost,
        s.snapshot_planned_load_minutes as plan_load_min,
        s.snapshot_planned_unload_minutes as plan_unload_min,
        
        s.vehicle_id,
        v.name as vehicle_name,
        
        s.driver_id,
        d.name as driver_name,
        
        s.route_id,
        r.name as route_name,
        r.origin_location_id,
        r.dest_location_id,
        
        l_orig.name as origin_name,
        l_orig.address_street as origin_address_street,
        l_orig.city as origin_city,
        l_orig.state as origin_state,
        
        l_dest.name as dest_name,
        l_dest.address_street as dest_address_street,
        l_dest.city as dest_city,
        l_dest.state as dest_state

    FROM scenarios s
    JOIN routes r ON s.route_id = r.route_id AND s.tenant_id = r.tenant_id
    JOIN locations l_orig ON r.origin_location_id = l_orig.location_id AND l_orig.tenant_id = p_tenant_id
    JOIN locations l_dest ON r.dest_location_id = l_dest.location_id AND l_dest.tenant_id = p_tenant_id
    LEFT JOIN vehicles v ON s.vehicle_id = v.vehicle_id AND s.tenant_id = v.tenant_id
    LEFT JOIN drivers d ON s.driver_id = d.driver_id AND s.tenant_id = d.tenant_id
    WHERE s.scenario_id = p_scenario_id AND s.tenant_id = p_tenant_id;

    -- 2. Manifest Items
    SELECT 
        mi.manifest_item_id,
        mi.item_name as product_name,
        mi.quantity_loaded,
        mi.snapshot_items_per_unit as items_per_unit,
        mi.snapshot_unit_weight as unit_weight_lbs,
        mi.snapshot_unit_volume as unit_volume,
        mi.snapshot_cost_per_item as cost_per_item,
        mi.snapshot_price_per_item as price_per_item,
        
        -- Join to get product_code (used as product_id in frontend)
        pm.product_code as product_id
        
    FROM manifest_items mi
    LEFT JOIN products_master pm ON mi.item_name = pm.name AND mi.tenant_id = pm.tenant_id
    WHERE mi.scenario_id = p_scenario_id AND mi.tenant_id = p_tenant_id;

END $$

DELIMITER ;