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

    -- 1. Snapshot Cargo Details
    SELECT cost_per_item, items_per_handling_unit, unit_weight_lbs
    INTO v_cost, v_items, v_weight
    FROM supply WHERE supply_id = p_supply_id;

    -- 2. Insert Item 
    -- (This fires the 'trg_manifest_insert' Trigger, reducing Supply automatically)
    INSERT INTO manifest_items (
        scenario_id, supply_id, demand_id, quantity_loaded,
        snapshot_cost_per_item, snapshot_items_per_unit, snapshot_unit_weight
    ) VALUES (
        p_scenario_id, p_supply_id, p_demand_id, p_qty_to_load,
        v_cost, v_items, v_weight
    );
END$$

DELIMITER ;