DELIMITER $$

DROP PROCEDURE IF EXISTS delete_location $$
CREATE PROCEDURE delete_location(
    IN p_location_id INT
)
BEGIN
    DELETE FROM locations
    WHERE location_id = p_location_id;
END $$

DROP PROCEDURE IF EXISTS delete_product_master $$
CREATE PROCEDURE delete_product_master(
    IN p_product_code VARCHAR(50)
)
BEGIN
    DELETE FROM products_master
    WHERE product_code = p_product_code;
END $$

DROP PROCEDURE IF EXISTS delete_driver $$
CREATE PROCEDURE delete_driver(
    IN p_driver_id INT
)
BEGIN
    DELETE FROM drivers
    WHERE driver_id = p_driver_id;
END $$

DROP PROCEDURE IF EXISTS delete_vehicle $$
CREATE PROCEDURE delete_vehicle(
    IN p_vehicle_id INT
)
BEGIN
    DELETE FROM vehicles
    WHERE vehicle_id = p_vehicle_id;
END $$

DROP PROCEDURE IF EXISTS delete_entity $$
CREATE PROCEDURE delete_entity(
    IN p_entity_id INT
)
BEGIN
    DELETE FROM entities
    WHERE entity_id = p_entity_id;
END $$

DROP PROCEDURE IF EXISTS delete_supply $$
CREATE PROCEDURE delete_supply(
    IN p_supply_id INT
)
BEGIN
    DELETE FROM supply
    WHERE supply_id = p_supply_id;
END $$

DROP PROCEDURE IF EXISTS delete_demand $$
CREATE PROCEDURE delete_demand(
    IN p_demand_id INT
)
BEGIN
    DELETE FROM demand
    WHERE demand_id = p_demand_id;
END $$

DROP PROCEDURE IF EXISTS delete_route $$
CREATE PROCEDURE delete_route(
    IN p_route_id INT
)
BEGIN
    DELETE FROM routes
    WHERE route_id = p_route_id;
END $$

DROP PROCEDURE IF EXISTS delete_scenario $$
CREATE PROCEDURE delete_scenario(
    IN p_scenario_id INT
)
BEGIN
    DELETE FROM scenarios
    WHERE scenario_id = p_scenario_id;
END $$

DROP PROCEDURE IF EXISTS delete_manifest_item $$
CREATE PROCEDURE delete_manifest_item(
    IN p_manifest_item_id INT
)
BEGIN
    DELETE FROM manifest_items
    WHERE manifest_item_id = p_manifest_item_id;
END $$

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
