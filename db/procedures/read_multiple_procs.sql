
-- Simple read procedures that allow for user to limit the number of inputs or 
-- specific columns. 
DELIMITER $$

DROP PROCEDURE IF EXISTS view_locations $$
CREATE PROCEDURE view_locations(
    IN p_columns TEXT,
    IN p_limit INT
)
BEGIN
    SET @cols := IF(p_columns IS NULL OR p_columns = '', '*', p_columns);
    SET @sql := CONCAT('SELECT ', @cols, ' FROM locations ORDER BY location_id');
    IF p_limit IS NOT NULL AND p_limit > 0 THEN
        SET @sql := CONCAT(@sql, ' LIMIT ', p_limit);
    END IF;
    PREPARE stmt FROM @sql;
    EXECUTE stmt;
    DEALLOCATE PREPARE stmt;
END $$

DROP PROCEDURE IF EXISTS view_products_master $$
CREATE PROCEDURE view_products_master(
    IN p_columns TEXT,
    IN p_limit INT
)
BEGIN
    SET @cols := IF(p_columns IS NULL OR p_columns = '', '*', p_columns);
    SET @sql := CONCAT('SELECT ', @cols, ' FROM products_master ORDER BY product_code');
    IF p_limit IS NOT NULL AND p_limit > 0 THEN
        SET @sql := CONCAT(@sql, ' LIMIT ', p_limit);
    END IF;
    PREPARE stmt FROM @sql;
    EXECUTE stmt;
    DEALLOCATE PREPARE stmt;
END $$

DROP PROCEDURE IF EXISTS view_drivers $$
CREATE PROCEDURE view_drivers(
    IN p_columns TEXT,
    IN p_limit INT
)
BEGIN
    SET @cols := IF(p_columns IS NULL OR p_columns = '', '*', p_columns);
    SET @sql := CONCAT('SELECT ', @cols, ' FROM drivers ORDER BY driver_id');
    IF p_limit IS NOT NULL AND p_limit > 0 THEN
        SET @sql := CONCAT(@sql, ' LIMIT ', p_limit);
    END IF;
    PREPARE stmt FROM @sql;
    EXECUTE stmt;
    DEALLOCATE PREPARE stmt;
END $$

DROP PROCEDURE IF EXISTS view_vehicles $$
CREATE PROCEDURE view_vehicles(
    IN p_columns TEXT,
    IN p_limit INT
)
BEGIN
    SET @cols := IF(p_columns IS NULL OR p_columns = '', '*', p_columns);
    SET @sql := CONCAT('SELECT ', @cols, ' FROM vehicles ORDER BY vehicle_id');
    IF p_limit IS NOT NULL AND p_limit > 0 THEN
        SET @sql := CONCAT(@sql, ' LIMIT ', p_limit);
    END IF;
    PREPARE stmt FROM @sql;
    EXECUTE stmt;
    DEALLOCATE PREPARE stmt;
END $$

DROP PROCEDURE IF EXISTS view_entities $$
CREATE PROCEDURE view_entities(
    IN p_columns TEXT,
    IN p_limit INT
)
BEGIN
    SET @cols := IF(p_columns IS NULL OR p_columns = '', '*', p_columns);
    SET @sql := CONCAT('SELECT ', @cols, ' FROM entities ORDER BY entity_id');
    IF p_limit IS NOT NULL AND p_limit > 0 THEN
        SET @sql := CONCAT(@sql, ' LIMIT ', p_limit);
    END IF;
    PREPARE stmt FROM @sql;
    EXECUTE stmt;
    DEALLOCATE PREPARE stmt;
END $$

DROP PROCEDURE IF EXISTS view_supply $$
CREATE PROCEDURE view_supply(
    IN p_columns TEXT,
    IN p_limit INT
)
BEGIN
    SET @cols := IF(p_columns IS NULL OR p_columns = '', '*', p_columns);
    SET @sql := CONCAT('SELECT ', @cols, ' FROM supply ORDER BY supply_id');
    IF p_limit IS NOT NULL AND p_limit > 0 THEN
        SET @sql := CONCAT(@sql, ' LIMIT ', p_limit);
    END IF;
    PREPARE stmt FROM @sql;
    EXECUTE stmt;
    DEALLOCATE PREPARE stmt;
END $$

DROP PROCEDURE IF EXISTS view_demand $$
CREATE PROCEDURE view_demand(
    IN p_columns TEXT,
    IN p_limit INT
)
BEGIN
    SET @cols := IF(p_columns IS NULL OR p_columns = '', '*', p_columns);
    SET @sql := CONCAT('SELECT ', @cols, ' FROM demand ORDER BY demand_id');
    IF p_limit IS NOT NULL AND p_limit > 0 THEN
        SET @sql := CONCAT(@sql, ' LIMIT ', p_limit);
    END IF;
    PREPARE stmt FROM @sql;
    EXECUTE stmt;
    DEALLOCATE PREPARE stmt;
END $$

DROP PROCEDURE IF EXISTS view_routes $$
CREATE PROCEDURE view_routes(
    IN p_columns TEXT,
    IN p_limit INT
)
BEGIN
    SET @cols := IF(p_columns IS NULL OR p_columns = '', '*', p_columns);
    SET @sql := CONCAT('SELECT ', @cols, ' FROM routes ORDER BY route_id');
    IF p_limit IS NOT NULL AND p_limit > 0 THEN
        SET @sql := CONCAT(@sql, ' LIMIT ', p_limit);
    END IF;
    PREPARE stmt FROM @sql;
    EXECUTE stmt;
    DEALLOCATE PREPARE stmt;
END $$

DROP PROCEDURE IF EXISTS view_scenarios $$
CREATE PROCEDURE view_scenarios(
    IN p_columns TEXT,
    IN p_limit INT
)
BEGIN
    SET @cols := IF(p_columns IS NULL OR p_columns = '', '*', p_columns);
    SET @sql := CONCAT('SELECT ', @cols, ' FROM scenarios ORDER BY scenario_id');
    IF p_limit IS NOT NULL AND p_limit > 0 THEN
        SET @sql := CONCAT(@sql, ' LIMIT ', p_limit);
    END IF;
    PREPARE stmt FROM @sql;
    EXECUTE stmt;
    DEALLOCATE PREPARE stmt;
END $$

DROP PROCEDURE IF EXISTS view_manifest_items $$
CREATE PROCEDURE view_manifest_items(
    IN p_columns TEXT,
    IN p_limit INT
)
BEGIN
    SET @cols := IF(p_columns IS NULL OR p_columns = '', '*', p_columns);
    SET @sql := CONCAT('SELECT ', @cols, ' FROM manifest_items ORDER BY manifest_item_id');
    IF p_limit IS NOT NULL AND p_limit > 0 THEN
        SET @sql := CONCAT(@sql, ' LIMIT ', p_limit);
    END IF;
    PREPARE stmt FROM @sql;
    EXECUTE stmt;
    DEALLOCATE PREPARE stmt;
END $$

DELIMITER ;
