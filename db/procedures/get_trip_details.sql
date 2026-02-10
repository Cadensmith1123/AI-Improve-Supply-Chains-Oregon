USE local_food_db;

DELIMITER $$

DROP PROCEDURE IF EXISTS get_trip_details$$

CREATE PROCEDURE get_trip_details(IN p_scenario_id INT)
BEGIN
    -- Result set 1: header repeated per line item
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

        COALESCE(p.name, mi.item_name) AS product_name,
        mi.quantity_loaded,
        mi.snapshot_items_per_unit AS items_per_unit,
        mi.snapshot_unit_weight AS unit_weight_lbs,
        mi.snapshot_unit_volume AS unit_volume,
        mi.snapshot_cost_per_item AS cost_per_item,
        mi.snapshot_price_per_item AS price_per_item,

        (mi.quantity_loaded * mi.snapshot_unit_weight) AS total_line_weight_lbs,
        (mi.quantity_loaded * mi.snapshot_unit_volume) AS total_line_volume,
        (mi.quantity_loaded * mi.snapshot_items_per_unit * mi.snapshot_cost_per_item) AS total_line_cogs,
        (mi.quantity_loaded * mi.snapshot_items_per_unit * mi.snapshot_price_per_item) AS total_line_revenue
    FROM scenarios s
    JOIN routes r ON s.route_id = r.route_id
    LEFT JOIN vehicles v ON s.vehicle_id = v.vehicle_id
    LEFT JOIN drivers d ON s.driver_id = d.driver_id
    LEFT JOIN manifest_items mi ON s.scenario_id = mi.scenario_id
    LEFT JOIN supply sup ON mi.supply_id = sup.supply_id
    LEFT JOIN products_master p ON sup.product_code = p.product_code
    WHERE s.scenario_id = p_scenario_id;

    -- Result set 2: Totals
    SELECT
        s.scenario_id,
        s.snapshot_total_revenue AS entered_revenue,
        COALESCE(SUM(mi.quantity_loaded * mi.snapshot_items_per_unit * mi.snapshot_price_per_item), 0) AS calculated_revenue,
        COALESCE(SUM(mi.quantity_loaded * mi.snapshot_items_per_unit * mi.snapshot_cost_per_item), 0) AS total_cogs,
        COALESCE(SUM(mi.quantity_loaded * mi.snapshot_unit_weight), 0) AS total_weight_lbs,
        COALESCE(SUM(mi.quantity_loaded * mi.snapshot_unit_volume), 0) AS total_volume,
        COUNT(mi.manifest_item_id) AS line_item_count
    FROM scenarios s
    LEFT JOIN manifest_items mi ON s.scenario_id = mi.scenario_id
    WHERE s.scenario_id = p_scenario_id
    GROUP BY s.scenario_id, s.snapshot_total_revenue;
END$$


DELIMITER ;