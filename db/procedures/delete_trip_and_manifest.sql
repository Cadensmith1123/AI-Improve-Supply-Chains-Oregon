USE local_food_db;

DELIMITER $$

DROP PROCEDURE IF EXISTS delete_plan$$

CREATE PROCEDURE delete_plan(IN p_scenario_id INT)
BEGIN
    -- 1. EXPLICITLY DELETE ITEMS FIRST TO TRIGGER INVENTORY BACK TO STOCK
    DELETE FROM manifest_items WHERE scenario_id = p_scenario_id;
    
    DELETE FROM scenarios WHERE scenario_id = p_scenario_id;
    
    SELECT CONCAT('Plan ', p_scenario_id, ' deleted and inventory explicitly restored.') as status;
END$$

DELIMITER ;