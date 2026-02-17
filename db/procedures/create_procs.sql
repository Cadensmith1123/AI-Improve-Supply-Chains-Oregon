DELIMITER $$

-- 1. Add Location
DROP PROCEDURE IF EXISTS add_location $$
CREATE PROCEDURE add_location(
    IN p_tenant_id INT,
    IN p_name VARCHAR(100),
    IN p_type VARCHAR(20),
    IN p_address VARCHAR(255),
    IN p_city VARCHAR(100),
    IN p_state VARCHAR(50),
    IN p_zip VARCHAR(20),
    IN p_phone VARCHAR(20),
    IN p_lat DECIMAL(10,8),
    IN p_lon DECIMAL(11,8),
    IN p_load_min INT,
    IN p_unload_min INT
)
BEGIN
    INSERT INTO locations (tenant_id, name, type, address_street, city, state, zip_code, phone, latitude, longitude, avg_load_minutes, avg_unload_minutes)
    VALUES (p_tenant_id, p_name, p_type, p_address, p_city, p_state, p_zip, p_phone, p_lat, p_lon, p_load_min, p_unload_min);
    SELECT LAST_INSERT_ID();
END $$

-- 2. Add Product Master
DROP PROCEDURE IF EXISTS add_product_master $$
CREATE PROCEDURE add_product_master(
    IN p_tenant_id INT,
    IN p_code VARCHAR(50),
    IN p_name VARCHAR(100),
    IN p_storage VARCHAR(10)
)
BEGIN
    INSERT INTO products_master (tenant_id, product_code, name, storage_type)
    VALUES (p_tenant_id, p_code, p_name, p_storage);
    SELECT p_code; -- Return the code as ID
END $$

-- 3. Add Driver
DROP PROCEDURE IF EXISTS add_driver $$
CREATE PROCEDURE add_driver(
    IN p_tenant_id INT,
    IN p_name VARCHAR(100),
    IN p_drive_wage DECIMAL(5,2),
    IN p_load_wage DECIMAL(5,2)
)
BEGIN
    INSERT INTO drivers (tenant_id, name, hourly_drive_wage, hourly_load_wage)
    VALUES (p_tenant_id, p_name, p_drive_wage, p_load_wage);
    SELECT LAST_INSERT_ID();
END $$

-- 4. Add Vehicle
DROP PROCEDURE IF EXISTS add_vehicle $$
CREATE PROCEDURE add_vehicle(
    IN p_tenant_id INT,
    IN p_name VARCHAR(100),
    IN p_mpg DECIMAL(4,1),
    IN p_depreciation DECIMAL(5,3),
    IN p_insurance DECIMAL(10,2),
    IN p_maintenance DECIMAL(10,2),
    IN p_weight DECIMAL(10,2),
    IN p_volume DECIMAL(10,2),
    IN p_storage VARCHAR(10)
)
BEGIN
    INSERT INTO vehicles (tenant_id, name, mpg, depreciation_per_mile, annual_insurance_cost, annual_maintenance_cost, max_weight_lbs, max_volume_cubic_ft, storage_type)
    VALUES (p_tenant_id, p_name, p_mpg, p_depreciation, p_insurance, p_maintenance, p_weight, p_volume, p_storage);
    SELECT LAST_INSERT_ID();
END $$

-- 5. Add Entity
DROP PROCEDURE IF EXISTS add_entity $$
CREATE PROCEDURE add_entity(
    IN p_tenant_id INT,
    IN p_name VARCHAR(100),
    IN p_min_profit DECIMAL(10,2)
)
BEGIN
    INSERT INTO entities (tenant_id, name, entity_min_profit)
    VALUES (p_tenant_id, p_name, p_min_profit);
    SELECT LAST_INSERT_ID();
END $$

-- 6. Add Supply
DROP PROCEDURE IF EXISTS add_supply $$
CREATE PROCEDURE add_supply(
    IN p_tenant_id INT,
    IN p_entity_id INT,
    IN p_location_id INT,
    IN p_product_code VARCHAR(50),
    IN p_qty DECIMAL(10,2),
    IN p_weight DECIMAL(10,2),
    IN p_volume DECIMAL(10,2),
    IN p_items_unit INT,
    IN p_cost DECIMAL(10,2)
)
BEGIN
    INSERT INTO supply (tenant_id, entity_id, location_id, product_code, quantity_available, unit_weight_lbs, unit_volume_cu_ft, items_per_handling_unit, cost_per_item)
    VALUES (p_tenant_id, p_entity_id, p_location_id, p_product_code, p_qty, p_weight, p_volume, p_items_unit, p_cost);
    SELECT LAST_INSERT_ID();
END $$

-- 7. Add Demand
DROP PROCEDURE IF EXISTS add_demand $$
CREATE PROCEDURE add_demand(
    IN p_tenant_id INT,
    IN p_location_id INT,
    IN p_product_code VARCHAR(50),
    IN p_qty DECIMAL(10,2),
    IN p_max_price DECIMAL(10,2)
)
BEGIN
    INSERT INTO demand (tenant_id, location_id, product_code, quantity_needed, max_price)
    VALUES (p_tenant_id, p_location_id, p_product_code, p_qty, p_max_price);
    SELECT LAST_INSERT_ID();
END $$

-- 8. Add Route
DROP PROCEDURE IF EXISTS add_route $$
CREATE PROCEDURE add_route(
    IN p_tenant_id INT,
    IN p_name VARCHAR(100),
    IN p_origin_id INT,
    IN p_dest_id INT
)
BEGIN
    INSERT INTO routes (tenant_id, name, origin_location_id, dest_location_id)
    VALUES (p_tenant_id, p_name, p_origin_id, p_dest_id);
    SELECT LAST_INSERT_ID();
END $$

-- 9. Add Manifest Item (Simple Insert, logic in python/other procs)
DROP PROCEDURE IF EXISTS add_manifest_item $$
CREATE PROCEDURE add_manifest_item(
    IN p_tenant_id INT,
    IN p_scenario_id INT,
    IN p_supply_id INT,
    IN p_demand_id INT,
    IN p_item_name VARCHAR(100),
    IN p_quantity_loaded DECIMAL(10,2),
    IN p_cost DECIMAL(10,2),
    IN p_items_per_unit INT,
    IN p_unit_weight DECIMAL(10,2),
    IN p_unit_volume DECIMAL(10,2),
    IN p_price DECIMAL(10,2)
)
BEGIN
    INSERT INTO manifest_items (tenant_id, scenario_id, supply_id, demand_id, item_name, quantity_loaded, snapshot_cost_per_item, snapshot_items_per_unit, snapshot_unit_weight, snapshot_unit_volume, snapshot_price_per_item)
    VALUES (p_tenant_id, p_scenario_id, p_supply_id, p_demand_id, p_item_name, p_quantity_loaded, p_cost, p_items_per_unit, p_unit_weight, p_unit_volume, p_price);
    SELECT LAST_INSERT_ID();
END $$

DELIMITER ;