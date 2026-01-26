DELIMITER $$

DROP PROCEDURE IF EXISTS add_trip_item$$

CREATE PROCEDURE add_trip_item(
    IN p_scenario_id INT,
    IN p_supply_id INT,
    IN p_demand_id INT,      -- Can be NULL if moving to storage
    IN p_qty_to_load DECIMAL(10,2)
)
BEGIN
    DECLARE v_cost DECIMAL(10,2);
    DECLARE v_items INT;
    DECLARE v_weight DECIMAL(8,2);
    DECLARE v_price DECIMAL(10,2); -- NEW: Variable for Price

    -- 1. Snapshot Cargo Details (From Supply)
    SELECT cost_per_item, items_per_handling_unit, unit_weight_lbs
    INTO v_cost, v_items, v_weight
    FROM supply WHERE supply_id = p_supply_id;

    -- 2. Snapshot Sale Price (From Demand, if it exists)
    IF p_demand_id IS NOT NULL THEN
        SELECT max_price INTO v_price 
        FROM demand WHERE demand_id = p_demand_id;
    ELSE
        SET v_price = NULL; -- Not a sale (e.g. Transfer to Storage)
    END IF;

    -- 3. Insert Item 
    INSERT INTO manifest_items (
        scenario_id, supply_id, demand_id, quantity_loaded,
        snapshot_cost_per_item, 
        snapshot_price_per_item, -- NEW: Insert the frozen price
        snapshot_items_per_unit, 
        snapshot_unit_weight
    ) VALUES (
        p_scenario_id, p_supply_id, p_demand_id, p_qty_to_load,
        v_cost, 
        v_price, 
        v_items, 
        v_weight
    );
END$$

DELIMITER ;