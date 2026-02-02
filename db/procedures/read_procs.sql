
-- Simple read procedures that allow for user to limit the number of inputs or 
-- specific columns and pass a JSON array of IDs to return.

DELIMITER $$

DROP PROCEDURE IF EXISTS view_locations $$
CREATE PROCEDURE view_locations(
    IN p_columns TEXT,
    IN p_limit INT,
    IN p_ids TEXT
)
BEGIN
    SET @cols := IF(p_columns IS NULL OR p_columns = '', '*', p_columns);
    SET @ids := p_ids;

    SET @sql := CONCAT(
        'SELECT ', @cols,
        ' FROM locations',
        ' WHERE (@ids IS NULL OR @ids = '''' OR FIND_IN_SET(CAST(location_id AS CHAR), @ids))',
        ' ORDER BY location_id'
    );

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
    IN p_limit INT,
    IN p_codes TEXT   -- comma-separated like 'APPLE01,BEEF02'
)
BEGIN
    SET @cols := IF(p_columns IS NULL OR p_columns = '', '*', p_columns);
    SET @codes := p_codes;

    SET @sql := CONCAT(
        'SELECT ', @cols,
        ' FROM products_master',
        ' WHERE (@codes IS NULL OR @codes = '''' OR FIND_IN_SET(product_code, @codes))',
        ' ORDER BY product_code'
    );

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
    IN p_limit INT,
    IN p_ids TEXT
)
BEGIN
    SET @cols := IF(p_columns IS NULL OR p_columns = '', '*', p_columns);
    SET @ids := p_ids;

    SET @sql := CONCAT(
        'SELECT ', @cols,
        ' FROM drivers',
        ' WHERE (@ids IS NULL OR @ids = '''' OR FIND_IN_SET(CAST(driver_id AS CHAR), @ids))',
        ' ORDER BY driver_id'
    );

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
    IN p_limit INT,
    IN p_ids TEXT
)
BEGIN
    SET @cols := IF(p_columns IS NULL OR p_columns = '', '*', p_columns);
    SET @ids := p_ids;

    SET @sql := CONCAT(
        'SELECT ', @cols,
        ' FROM vehicles',
        ' WHERE (@ids IS NULL OR @ids = '''' OR FIND_IN_SET(CAST(vehicle_id AS CHAR), @ids))',
        ' ORDER BY vehicle_id'
    );

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
    IN p_limit INT,
    IN p_ids TEXT
)
BEGIN
    SET @cols := IF(p_columns IS NULL OR p_columns = '', '*', p_columns);
    SET @ids := p_ids;

    SET @sql := CONCAT(
        'SELECT ', @cols,
        ' FROM entities',
        ' WHERE (@ids IS NULL OR @ids = '''' OR FIND_IN_SET(CAST(entity_id AS CHAR), @ids))',
        ' ORDER BY entity_id'
    );

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
    IN p_limit INT,
    IN p_ids TEXT
)
BEGIN
    SET @cols := IF(p_columns IS NULL OR p_columns = '', '*', p_columns);
    SET @ids := p_ids;

    SET @sql := CONCAT(
        'SELECT ', @cols,
        ' FROM supply',
        ' WHERE (@ids IS NULL OR @ids = '''' OR FIND_IN_SET(CAST(supply_id AS CHAR), @ids))',
        ' ORDER BY supply_id'
    );

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
    IN p_limit INT,
    IN p_ids TEXT
)
BEGIN
    SET @cols := IF(p_columns IS NULL OR p_columns = '', '*', p_columns);
    SET @ids := p_ids;

    SET @sql := CONCAT(
        'SELECT ', @cols,
        ' FROM demand',
        ' WHERE (@ids IS NULL OR @ids = '''' OR FIND_IN_SET(CAST(demand_id AS CHAR), @ids))',
        ' ORDER BY demand_id'
    );

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
    IN p_limit INT,
    IN p_ids TEXT
)
BEGIN
    SET @cols := IF(p_columns IS NULL OR p_columns = '', '*', p_columns);
    SET @ids := p_ids;

    SET @sql := CONCAT(
        'SELECT ', @cols,
        ' FROM routes',
        ' WHERE (@ids IS NULL OR @ids = '''' OR FIND_IN_SET(CAST(route_id AS CHAR), @ids))',
        ' ORDER BY route_id'
    );

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
    IN p_limit INT,
    IN p_ids TEXT
)
BEGIN
    SET @cols := IF(p_columns IS NULL OR p_columns = '', '*', p_columns);
    SET @ids := p_ids;

    SET @sql := CONCAT(
        'SELECT ', @cols,
        ' FROM scenarios',
        ' WHERE (@ids IS NULL OR @ids = '''' OR FIND_IN_SET(CAST(scenario_id AS CHAR), @ids))',
        ' ORDER BY scenario_id'
    );

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
    IN p_limit INT,
    IN p_ids TEXT
)
BEGIN
    SET @cols := IF(p_columns IS NULL OR p_columns = '', '*', p_columns);
    SET @ids := p_ids;

    SET @sql := CONCAT(
        'SELECT ', @cols,
        ' FROM manifest_items',
        ' WHERE (@ids IS NULL OR @ids = '''' OR FIND_IN_SET(CAST(manifest_item_id AS CHAR), @ids))',
        ' ORDER BY manifest_item_id'
    );

    IF p_limit IS NOT NULL AND p_limit > 0 THEN
        SET @sql := CONCAT(@sql, ' LIMIT ', p_limit);
    END IF;

    PREPARE stmt FROM @sql;
    EXECUTE stmt;
    DEALLOCATE PREPARE stmt;
END $$

DELIMITER ;
