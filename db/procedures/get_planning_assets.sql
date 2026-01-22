USE local_food_db;

DELIMITER $$

DROP PROCEDURE IF EXISTS get_planning_assets$$

CREATE PROCEDURE get_planning_assets()
BEGIN
    -- 1. AVAILABLE SUPPLY (The "Pick List")
    SELECT 
        s.supply_id,
        p.name AS product_name,
        l.name AS location_name,
        l.location_id,
        s.quantity_available, 
        
        -- Logistics Math
        s.unit_weight_lbs,    
        s.unit_volume_cu_ft,  
        
        -- Profit Math
        s.items_per_handling_unit, 
        s.cost_per_item            
    FROM supply s
    JOIN locations l ON s.location_id = l.location_id
    JOIN products_master p ON s.product_code = p.product_code
    WHERE s.quantity_available > 0;

    -- 2. OPEN DEMAND (The "Destinations")
    SELECT 
        d.demand_id,
        l.name AS location_name,
        l.location_id,
        p.name AS product_name,
        d.quantity_needed,
        d.max_price
    FROM demand d
    JOIN locations l ON d.location_id = l.location_id
    JOIN products_master p ON d.product_code = p.product_code;

    -- 3. VEHICLES (Constraints & Costs)
    SELECT 
        vehicle_id, name, 
        max_weight_lbs, max_volume_cubic_ft, storage_capability,
        mpg, depreciation_per_mile, annual_insurance_cost
    FROM vehicles;

    -- 4. DRIVERS (Wage Rates)
    SELECT 
        driver_id, name, 
        hourly_drive_wage, hourly_load_wage 
    FROM drivers;

    -- 5. ROUTES (The Map)
    SELECT route_id, name, origin_location_id, dest_location_id FROM routes;

    -- 6. LOCATIONS (Time & Space)
    -- Python uses Lat/Long for distance, and Avg Mins for time calc.
    SELECT
        location_id, name,
        latitude, longitude,
        avg_load_minutes,   -- NEW: Estimate loading time
        avg_unload_minutes  -- NEW: Estimate unloading time
    FROM locations;

END$$

DELIMITER ;