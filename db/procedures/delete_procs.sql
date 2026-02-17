DELIMITER $$

DROP PROCEDURE IF EXISTS delete_location $$
CREATE PROCEDURE delete_location(IN p_tenant_id INT, IN p_id INT)
BEGIN
    DELETE FROM locations WHERE location_id = p_id AND tenant_id = p_tenant_id;
END $$

DROP PROCEDURE IF EXISTS delete_product_master $$
CREATE PROCEDURE delete_product_master(IN p_tenant_id INT, IN p_id VARCHAR(50))
BEGIN
    DELETE FROM products_master WHERE product_code = p_id AND tenant_id = p_tenant_id;
END $$

DROP PROCEDURE IF EXISTS delete_driver $$
CREATE PROCEDURE delete_driver(IN p_tenant_id INT, IN p_id INT)
BEGIN
    DELETE FROM drivers WHERE driver_id = p_id AND tenant_id = p_tenant_id;
END $$

DROP PROCEDURE IF EXISTS delete_vehicle $$
CREATE PROCEDURE delete_vehicle(IN p_tenant_id INT, IN p_id INT)
BEGIN
    DELETE FROM vehicles WHERE vehicle_id = p_id AND tenant_id = p_tenant_id;
END $$

DROP PROCEDURE IF EXISTS delete_entity $$
CREATE PROCEDURE delete_entity(IN p_tenant_id INT, IN p_id INT)
BEGIN
    DELETE FROM entities WHERE entity_id = p_id AND tenant_id = p_tenant_id;
END $$

DROP PROCEDURE IF EXISTS delete_supply $$
CREATE PROCEDURE delete_supply(IN p_tenant_id INT, IN p_id INT)
BEGIN
    DELETE FROM supply WHERE supply_id = p_id AND tenant_id = p_tenant_id;
END $$

DROP PROCEDURE IF EXISTS delete_demand $$
CREATE PROCEDURE delete_demand(IN p_tenant_id INT, IN p_id INT)
BEGIN
    DELETE FROM demand WHERE demand_id = p_id AND tenant_id = p_tenant_id;
END $$

DROP PROCEDURE IF EXISTS delete_route $$
CREATE PROCEDURE delete_route(IN p_tenant_id INT, IN p_id INT)
BEGIN
    DELETE FROM routes WHERE route_id = p_id AND tenant_id = p_tenant_id;
END $$

DROP PROCEDURE IF EXISTS delete_plan $$
CREATE PROCEDURE delete_plan(IN p_tenant_id INT, IN p_id INT)
BEGIN
    DELETE FROM scenarios WHERE scenario_id = p_id AND tenant_id = p_tenant_id;
END $$

DROP PROCEDURE IF EXISTS delete_manifest_item $$
CREATE PROCEDURE delete_manifest_item(IN p_tenant_id INT, IN p_id INT)
BEGIN
    DELETE FROM manifest_items WHERE manifest_item_id = p_id AND tenant_id = p_tenant_id;
END $$

DELIMITER ;