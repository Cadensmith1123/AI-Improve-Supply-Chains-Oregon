DELIMITER $$

DROP PROCEDURE IF EXISTS add_location $$
CREATE PROCEDURE add_location(
    IN p_name VARCHAR(100),
    IN p_type ENUM('Hub','Store','Farm'),
    IN p_address_street VARCHAR(255),
    IN p_city VARCHAR(100),
    IN p_state VARCHAR(50),
    IN p_zip VARCHAR(20),
    IN p_phone VARCHAR(20),
    IN p_latitude DECIMAL(9,6),
    IN p_longitude DECIMAL(9,6),
    IN p_avg_load_minutes INT,
    IN p_avg_unload_minutes INT
)
BEGIN
    INSERT INTO locations (
        name, type, address_street, city, state, zip, phone,
        latitude, longitude, avg_load_minutes, avg_unload_minutes
    )
    VALUES (
        p_name, p_type, p_address_street, p_city, p_state, p_zip, p_phone,
        p_latitude, p_longitude, p_avg_load_minutes, p_avg_unload_minutes
    );
    SELECT LAST_INSERT_ID() AS new_id;
END $$

DROP PROCEDURE IF EXISTS add_product_master $$
CREATE PROCEDURE add_product_master(
    IN p_product_code VARCHAR(50),
    IN p_name VARCHAR(100),
    IN p_storage_type ENUM('Dry','Ref','Frz')
)
BEGIN
    INSERT INTO products_master (product_code, name, storage_type)
    VALUES (p_product_code, p_name, p_storage_type);
    SELECT p_product_code AS new_id;
END $$

DROP PROCEDURE IF EXISTS add_driver $$
CREATE PROCEDURE add_driver(
    IN p_name VARCHAR(100),
    IN p_hourly_drive_wage DECIMAL(5,2),
    IN p_hourly_load_wage DECIMAL(5,2)
)
BEGIN
    INSERT INTO drivers (name, hourly_drive_wage, hourly_load_wage)
    VALUES (p_name, p_hourly_drive_wage, p_hourly_load_wage);
    SELECT LAST_INSERT_ID() AS new_id;
END $$

DROP PROCEDURE IF EXISTS add_vehicle $$
CREATE PROCEDURE add_vehicle(
    IN p_name VARCHAR(100),
    IN p_mpg DECIMAL(4,1),
    IN p_depreciation_per_mile DECIMAL(10,2),
    IN p_annual_insurance_cost DECIMAL(10,2),
    IN p_max_weight_lbs INT,
    IN p_max_volume_cubic_ft INT,
    IN p_storage_capability ENUM('Dry','Ref','Frz','Multi')
)
BEGIN
    INSERT INTO vehicles (
        name, mpg, depreciation_per_mile, annual_insurance_cost,
        max_weight_lbs, max_volume_cubic_ft, storage_capability
    )
    VALUES (
        p_name, p_mpg, p_depreciation_per_mile, p_annual_insurance_cost,
        p_max_weight_lbs, p_max_volume_cubic_ft, p_storage_capability
    );
    SELECT LAST_INSERT_ID() AS new_id;
END $$

DROP PROCEDURE IF EXISTS add_entity $$
CREATE PROCEDURE add_entity(
    IN p_name VARCHAR(100),
    IN p_entity_min_profit INT
)
BEGIN
    INSERT INTO entities (name, entity_min_profit)
    VALUES (p_name, p_entity_min_profit);
    SELECT LAST_INSERT_ID() AS new_id;
END $$

DROP PROCEDURE IF EXISTS add_supply $$
CREATE PROCEDURE add_supply(
    IN p_entity_id INT,
    IN p_location_id INT,
    IN p_product_code VARCHAR(50),
    IN p_quantity_available DECIMAL(10,2),
    IN p_unit_weight_lbs DECIMAL(8,2),
    IN p_unit_volume_cu_ft DECIMAL(8,2),
    IN p_items_per_handling_unit INT,
    IN p_cost_per_item DECIMAL(10,2)
)
BEGIN
    INSERT INTO supply (
        entity_id, location_id, product_code,
        quantity_available, unit_weight_lbs, unit_volume_cu_ft,
        items_per_handling_unit, cost_per_item
    )
    VALUES (
        p_entity_id, p_location_id, p_product_code,
        p_quantity_available, p_unit_weight_lbs, p_unit_volume_cu_ft,
        p_items_per_handling_unit, p_cost_per_item
    );
    SELECT LAST_INSERT_ID() AS new_id;
END $$

DROP PROCEDURE IF EXISTS add_demand $$
CREATE PROCEDURE add_demand(
    IN p_location_id INT,
    IN p_product_code VARCHAR(50),
    IN p_quantity_needed DECIMAL(10,2),
    IN p_max_price DECIMAL(10,2)
)
BEGIN
    INSERT INTO demand (location_id, product_code, quantity_needed, max_price)
    VALUES (p_location_id, p_product_code, p_quantity_needed, p_max_price);
    SELECT LAST_INSERT_ID() AS new_id;
END $$

DROP PROCEDURE IF EXISTS add_route $$
CREATE PROCEDURE add_route(
    IN p_name VARCHAR(100),
    IN p_origin_location_id INT,
    IN p_dest_location_id INT
)
BEGIN
    INSERT INTO routes (name, origin_location_id, dest_location_id)
    VALUES (p_name, p_origin_location_id, p_dest_location_id);
    SELECT LAST_INSERT_ID() AS new_id;
END $$

DROP PROCEDURE IF EXISTS add_scenario $$
CREATE PROCEDURE add_scenario(
    IN p_route_id INT,
    IN p_vehicle_id INT,
    IN p_driver_id INT,
    IN p_run_date DATE,
    IN p_snapshot_driver_wage DECIMAL(5,2),
    IN p_snapshot_driver_load_wage DECIMAL(5,2),
    IN p_snapshot_vehicle_mpg DECIMAL(4,1),
    IN p_snapshot_gas_price DECIMAL(4,2),
    IN p_snapshot_daily_insurance DECIMAL(10,2),
    IN p_snapshot_planned_load_minutes INT,
    IN p_snapshot_planned_unload_minutes INT,
    IN p_actual_load_minutes INT,
    IN p_actual_unload_minutes INT,
    IN p_snapshot_total_revenue DECIMAL(4,2)
)
BEGIN
    INSERT INTO scenarios (
        route_id, vehicle_id, driver_id, run_date,
        snapshot_driver_wage, snapshot_driver_load_wage, snapshot_vehicle_mpg,
        snapshot_gas_price, snapshot_daily_insurance,
        snapshot_planned_load_minutes, snapshot_planned_unload_minutes,
        actual_load_minutes, actual_unload_minutes,
        snapshot_total_revenue
    )
    VALUES (
        p_route_id, p_vehicle_id, p_driver_id, p_run_date,
        p_snapshot_driver_wage, p_snapshot_driver_load_wage, p_snapshot_vehicle_mpg,
        p_snapshot_gas_price, p_snapshot_daily_insurance,
        p_snapshot_planned_load_minutes, p_snapshot_planned_unload_minutes,
        p_actual_load_minutes, p_actual_unload_minutes,
        p_snapshot_total_revenue
    );
    SELECT LAST_INSERT_ID() AS new_id;
END $$

DELIMITER $$

DROP PROCEDURE IF EXISTS add_manifest_item$$

CREATE PROCEDURE add_manifest_item(
    IN p_scenario_id INT,
    IN p_supply_id INT,
    IN p_demand_id INT,
    IN p_item_name VARCHAR(100),
    IN p_quantity_loaded DECIMAL(10,2),
    IN p_snapshot_cost_per_item DECIMAL(10,2),
    IN p_snapshot_items_per_unit INT,
    IN p_snapshot_unit_weight DECIMAL(8,2),
    IN p_snapshot_price_per_item DECIMAL(10,2)
)
BEGIN
    INSERT INTO manifest_items (
        scenario_id, supply_id, demand_id, item_name,
        quantity_loaded,
        snapshot_cost_per_item, snapshot_items_per_unit,
        snapshot_unit_weight, snapshot_price_per_item
    )
    VALUES (
        p_scenario_id, 
        p_supply_id, 
        p_demand_id,
        p_item_name,
        p_quantity_loaded,
        p_snapshot_cost_per_item, p_snapshot_items_per_unit,
        p_snapshot_unit_weight, p_snapshot_price_per_item
    );
    SELECT LAST_INSERT_ID() AS new_id;
END$$


DELIMITER ;
