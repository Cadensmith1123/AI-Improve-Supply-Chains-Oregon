USE local_food_db;

DELIMITER $$

DROP PROCEDURE IF EXISTS get_trip_details$$

CREATE PROCEDURE get_trip_details(IN p_scenario_id INT)
BEGIN
    SELECT 
        -- TRIP HEADER
        s.scenario_id,
        s.run_date,
        r.name AS route_name,
        v.name AS vehicle_name,
        d.name AS driver_name,
        
        -- FROZEN FINANCIALS
        s.snapshot_driver_wage AS driver_drive_rate,
        s.snapshot_driver_load_wage AS driver_load_rate,
        s.snapshot_vehicle_mpg AS vehicle_mpg,
        s.snapshot_gas_price AS gas_price,
        s.snapshot_daily_insurance AS daily_insurance,

        -- FROZEN TIME ESTIMATES
        s.snapshot_planned_load_minutes AS plan_load_min,
        s.snapshot_planned_unload_minutes AS plan_unload_min,
        
        -- MANIFEST LINE ITEMS
        COALESCE(p.name, mi.item_name) AS product_name,
        mi.quantity_loaded,
        mi.snapshot_unit_weight AS unit_weight_lbs,
        mi.snapshot_items_per_unit AS items_per_unit,
        
        -- UNIT ECONOMICS (Cost vs. Price)
        mi.snapshot_cost_per_item AS cost_per_item,
        mi.snapshot_price_per_item AS price_per_item,
        
        -- CALCULATED TOTALS (For Quick Verification)
        (mi.quantity_loaded * mi.snapshot_unit_weight) AS total_line_weight_lbs,
        
        -- Total Cost of Goods Sold (Expenses)
        (mi.quantity_loaded * mi.snapshot_items_per_unit * mi.snapshot_cost_per_item) AS total_line_cogs,
        
        -- Total Revenue (Income) - NEW
        -- Returns NULL if this is just a transfer (no sale price)
        (mi.quantity_loaded * mi.snapshot_items_per_unit * mi.snapshot_price_per_item) AS total_line_revenue

    FROM scenarios s
    JOIN routes r ON s.route_id = r.route_id
    LEFT JOIN vehicles v ON s.vehicle_id = v.vehicle_id
    LEFT JOIN drivers d ON s.driver_id = d.driver_id
    -- LEFT JOIN manifest items
    LEFT JOIN manifest_items mi ON s.scenario_id = mi.scenario_id
    LEFT JOIN supply sup ON mi.supply_id = sup.supply_id
    LEFT JOIN products_master p ON sup.product_code = p.product_code
    
    WHERE s.scenario_id = p_scenario_id;
END$$

DELIMITER ;