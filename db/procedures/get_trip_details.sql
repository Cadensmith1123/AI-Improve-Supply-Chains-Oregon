DELIMITER $$

DROP PROCEDURE IF EXISTS get_trip_details $$

CREATE PROCEDURE get_trip_details(
    IN p_tenant_id INT,
    IN p_scenario_id INT
)
BEGIN
    -- 1. Header + Items Joined
    SELECT 
        s.scenario_id,
        s.run_date,
        r.name AS route_name,
        v.name AS vehicle_name,
        d.name AS driver_name,
        
        s.snapshot_driver_wage AS driver_drive_rate,
        s.snapshot_driver_load_wage AS driver_load_rate,
        s.snapshot_vehicle_mpg AS vehicle_mpg,
        s.snapshot_gas_price AS gas_price,
        s.snapshot_daily_insurance AS daily_insurance,
        s.snapshot_daily_maintenance_cost AS daily_maintenance_cost,
        s.snapshot_total_revenue AS entered_revenue,
        s.snapshot_planned_load_minutes AS plan_load_min,
        s.snapshot_planned_unload_minutes AS plan_unload_min,

        mi.item_name AS product_name,
        mi.quantity_loaded,
        mi.snapshot_items_per_unit AS items_per_unit,
        mi.snapshot_unit_weight AS unit_weight_lbs,
        mi.snapshot_unit_volume AS unit_volume,
        mi.snapshot_cost_per_item AS cost_per_item,
        mi.snapshot_price_per_item AS price_per_item

    FROM scenarios s
    LEFT JOIN routes r ON s.route_id = r.route_id AND s.tenant_id = r.tenant_id
    LEFT JOIN vehicles v ON s.vehicle_id = v.vehicle_id AND s.tenant_id = v.tenant_id
    LEFT JOIN drivers d ON s.driver_id = d.driver_id AND s.tenant_id = d.tenant_id
    LEFT JOIN manifest_items mi ON s.scenario_id = mi.scenario_id AND s.tenant_id = mi.tenant_id
    WHERE s.scenario_id = p_scenario_id AND s.tenant_id = p_tenant_id;

END $$

DELIMITER ;