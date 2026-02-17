DELIMITER $$

DROP PROCEDURE IF EXISTS view_locations $$
CREATE PROCEDURE view_locations(IN p_tenant_id INT, IN p_cols TEXT, IN p_limit INT, IN p_ids TEXT)
BEGIN
    SET @sql = CONCAT('SELECT ', COALESCE(p_cols, '*'), ' FROM locations WHERE tenant_id = ', p_tenant_id);
    IF p_ids IS NOT NULL THEN SET @sql = CONCAT(@sql, ' AND location_id IN (', p_ids, ')'); END IF;
    IF p_limit IS NOT NULL THEN SET @sql = CONCAT(@sql, ' LIMIT ', p_limit); END IF;
    PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;
END $$

DROP PROCEDURE IF EXISTS view_products_master $$
CREATE PROCEDURE view_products_master(IN p_tenant_id INT, IN p_cols TEXT, IN p_limit INT, IN p_ids TEXT)
BEGIN
    SET @sql = CONCAT('SELECT ', COALESCE(p_cols, '*'), ' FROM products_master WHERE tenant_id = ', p_tenant_id);
    IF p_ids IS NOT NULL THEN 
        -- Handle string IDs safely usually, but for simplicity in dynamic SQL:
        SET @sql = CONCAT(@sql, ' AND product_code IN (', p_ids, ')'); 
    END IF;
    IF p_limit IS NOT NULL THEN SET @sql = CONCAT(@sql, ' LIMIT ', p_limit); END IF;
    PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;
END $$

DROP PROCEDURE IF EXISTS view_drivers $$
CREATE PROCEDURE view_drivers(IN p_tenant_id INT, IN p_cols TEXT, IN p_limit INT, IN p_ids TEXT)
BEGIN
    SET @sql = CONCAT('SELECT ', COALESCE(p_cols, '*'), ' FROM drivers WHERE tenant_id = ', p_tenant_id);
    IF p_ids IS NOT NULL THEN SET @sql = CONCAT(@sql, ' AND driver_id IN (', p_ids, ')'); END IF;
    IF p_limit IS NOT NULL THEN SET @sql = CONCAT(@sql, ' LIMIT ', p_limit); END IF;
    PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;
END $$

DROP PROCEDURE IF EXISTS view_vehicles $$
CREATE PROCEDURE view_vehicles(IN p_tenant_id INT, IN p_cols TEXT, IN p_limit INT, IN p_ids TEXT)
BEGIN
    SET @sql = CONCAT('SELECT ', COALESCE(p_cols, '*'), ' FROM vehicles WHERE tenant_id = ', p_tenant_id);
    IF p_ids IS NOT NULL THEN SET @sql = CONCAT(@sql, ' AND vehicle_id IN (', p_ids, ')'); END IF;
    IF p_limit IS NOT NULL THEN SET @sql = CONCAT(@sql, ' LIMIT ', p_limit); END IF;
    PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;
END $$

DROP PROCEDURE IF EXISTS view_entities $$
CREATE PROCEDURE view_entities(IN p_tenant_id INT, IN p_cols TEXT, IN p_limit INT, IN p_ids TEXT)
BEGIN
    SET @sql = CONCAT('SELECT ', COALESCE(p_cols, '*'), ' FROM entities WHERE tenant_id = ', p_tenant_id);
    IF p_ids IS NOT NULL THEN SET @sql = CONCAT(@sql, ' AND entity_id IN (', p_ids, ')'); END IF;
    IF p_limit IS NOT NULL THEN SET @sql = CONCAT(@sql, ' LIMIT ', p_limit); END IF;
    PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;
END $$

DROP PROCEDURE IF EXISTS view_supply $$
CREATE PROCEDURE view_supply(IN p_tenant_id INT, IN p_cols TEXT, IN p_limit INT, IN p_ids TEXT)
BEGIN
    SET @sql = CONCAT('SELECT ', COALESCE(p_cols, '*'), ' FROM supply WHERE tenant_id = ', p_tenant_id);
    IF p_ids IS NOT NULL THEN SET @sql = CONCAT(@sql, ' AND supply_id IN (', p_ids, ')'); END IF;
    IF p_limit IS NOT NULL THEN SET @sql = CONCAT(@sql, ' LIMIT ', p_limit); END IF;
    PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;
END $$

DROP PROCEDURE IF EXISTS view_demand $$
CREATE PROCEDURE view_demand(IN p_tenant_id INT, IN p_cols TEXT, IN p_limit INT, IN p_ids TEXT)
BEGIN
    SET @sql = CONCAT('SELECT ', COALESCE(p_cols, '*'), ' FROM demand WHERE tenant_id = ', p_tenant_id);
    IF p_ids IS NOT NULL THEN SET @sql = CONCAT(@sql, ' AND demand_id IN (', p_ids, ')'); END IF;
    IF p_limit IS NOT NULL THEN SET @sql = CONCAT(@sql, ' LIMIT ', p_limit); END IF;
    PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;
END $$

DROP PROCEDURE IF EXISTS view_routes $$
CREATE PROCEDURE view_routes(IN p_tenant_id INT, IN p_cols TEXT, IN p_limit INT, IN p_ids TEXT)
BEGIN
    SET @sql = CONCAT('SELECT ', COALESCE(p_cols, '*'), ' FROM routes WHERE tenant_id = ', p_tenant_id);
    IF p_ids IS NOT NULL THEN SET @sql = CONCAT(@sql, ' AND route_id IN (', p_ids, ')'); END IF;
    IF p_limit IS NOT NULL THEN SET @sql = CONCAT(@sql, ' LIMIT ', p_limit); END IF;
    PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;
END $$

DROP PROCEDURE IF EXISTS view_scenarios $$
CREATE PROCEDURE view_scenarios(IN p_tenant_id INT, IN p_cols TEXT, IN p_limit INT, IN p_ids TEXT)
BEGIN
    SET @sql = CONCAT('SELECT ', COALESCE(p_cols, '*'), ' FROM scenarios WHERE tenant_id = ', p_tenant_id);
    IF p_ids IS NOT NULL THEN SET @sql = CONCAT(@sql, ' AND scenario_id IN (', p_ids, ')'); END IF;
    IF p_limit IS NOT NULL THEN SET @sql = CONCAT(@sql, ' LIMIT ', p_limit); END IF;
    PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;
END $$

DROP PROCEDURE IF EXISTS view_manifest_items $$
CREATE PROCEDURE view_manifest_items(IN p_tenant_id INT, IN p_cols TEXT, IN p_limit INT, IN p_ids TEXT)
BEGIN
    SET @sql = CONCAT('SELECT ', COALESCE(p_cols, '*'), ' FROM manifest_items WHERE tenant_id = ', p_tenant_id);
    IF p_ids IS NOT NULL THEN SET @sql = CONCAT(@sql, ' AND manifest_item_id IN (', p_ids, ')'); END IF;
    IF p_limit IS NOT NULL THEN SET @sql = CONCAT(@sql, ' LIMIT ', p_limit); END IF;
    PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;
END $$

DELIMITER ;