DELIMITER $$

DROP PROCEDURE IF EXISTS update_location $$
CREATE PROCEDURE update_location(
    IN p_location_id INT,
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
    UPDATE locations
    SET
        name = p_name,
        type = p_type,
        address_street = p_address_street,
        city = p_city,
        state = p_state,
        zip = p_zip,
        phone = p_phone,
        latitude = p_latitude,
        longitude = p_longitude,
        avg_load_minutes = p_avg_load_minutes,
        avg_unload_minutes = p_avg_unload_minutes
    WHERE location_id = p_location_id;
END $$

DROP PROCEDURE IF EXISTS update_product_master $$
CREATE PROCEDURE update_product_master(
    IN p_product_code VARCHAR(50),
    IN p_name VARCHAR(100),
    IN p_storage_type ENUM('Dry','Ref','Frz')
)
BEGIN
    UPDATE products_master
    SET
        name = p_name,
        storage_type = p_storage_type
    WHERE product_code = p_product_code;
END $$

DROP PROCEDURE IF EXISTS update_driver $$
CREATE PROCEDURE update_driver(
    IN p_driver_id INT,
    IN p_name VARCHAR(100),
    IN p_hourly_drive_wage DECIMAL(5,2),
    IN p_hourly_load_wage DECIMAL(5,2)
)
BEGIN
    UPDATE drivers
    SET
        name = p_name,
        hourly_drive_wage = p_hourly_drive_wage,
        hourly_load_wage = p_hourly_load_wage
    WHERE driver_id = p_driver_id;
END $$

DROP PROCEDURE IF EXISTS update_vehicle $$
CREATE PROCEDURE update_vehicle(
    IN p_vehicle_id INT,
    IN p_name VARCHAR(100),
    IN p_mpg DECIMAL(4,1),
    IN p_depreciation_per_mile DECIMAL(10,2),
    IN p_annual_insurance_cost DECIMAL(10,2),
    IN p_max_weight_lbs INT,
    IN p_max_volume_cubic_ft INT,
    IN p_storage_capability ENUM('Dry','Ref','Frz','Multi')
)
BEGIN
    UPDATE vehicles
    SET
        name = p_name,
        mpg = p_mpg,
        depreciation_per_mile = p_depreciation_per_mile,
        annual_insurance_cost = p_annual_insurance_cost,
        max_weight_lbs = p_max_weight_lbs,
        max_volume_cubic_ft = p_max_volume_cubic_ft,
        storage_capability = p_storage_capability
    WHERE vehicle_id = p_vehicle_id;
END $$

DROP PROCEDURE IF EXISTS update_entity $$
CREATE PROCEDURE update_entity(
    IN p_entity_id INT,
    IN p_name VARCHAR(100),
    IN p_entity_min_profit INT
)
BEGIN
    UPDATE entities
    SET
        name = p_name,
        entity_min_profit = p_entity_min_profit
    WHERE entity_id = p_entity_id;
END $$

DROP PROCEDURE IF EXISTS update_supply $$
CREATE PROCEDURE update_supply(
    IN p_supply_id INT,
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
    UPDATE supply
    SET
        entity_id = p_entity_id,
        location_id = p_location_id,
        product_code = p_product_code,
        quantity_available = p_quantity_available,
        unit_weight_lbs = p_unit_weight_lbs,
        unit_volume_cu_ft = p_unit_volume_cu_ft,
        items_per_handling_unit = p_items_per_handling_unit,
        cost_per_item = p_cost_per_item
    WHERE supply_id = p_supply_id;
END $$

DROP PROCEDURE IF EXISTS update_demand $$
CREATE PROCEDURE update_demand(
    IN p_demand_id INT,
    IN p_location_id INT,
    IN p_product_code VARCHAR(50),
    IN p_quantity_needed DECIMAL(10,2),
    IN p_max_price DECIMAL(10,2)
)
BEGIN
    UPDATE demand
    SET
        location_id = p_location_id,
        product_code = p_product_code,
        quantity_needed = p_quantity_needed,
        max_price = p_max_price
    WHERE demand_id = p_demand_id;
END $$

DROP PROCEDURE IF EXISTS update_route $$
CREATE PROCEDURE update_route(
    IN p_route_id INT,
    IN p_name VARCHAR(100),
    IN p_origin_location_id INT,
    IN p_dest_location_id INT
)
BEGIN
    UPDATE routes
    SET
        name = p_name,
        origin_location_id = p_origin_location_id,
        dest_location_id = p_dest_location_id
    WHERE route_id = p_route_id;
END $$

DROP PROCEDURE IF EXISTS update_scenario $$
CREATE PROCEDURE update_scenario(
    IN p_scenario_id INT,
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
    UPDATE scenarios
    SET
        route_id = p_route_id,
        vehicle_id = p_vehicle_id,
        driver_id = p_driver_id,
        run_date = p_run_date,
        snapshot_driver_wage = p_snapshot_driver_wage,
        snapshot_driver_load_wage = p_snapshot_driver_load_wage,
        snapshot_vehicle_mpg = p_snapshot_vehicle_mpg,
        snapshot_gas_price = p_snapshot_gas_price,
        snapshot_daily_insurance = p_snapshot_daily_insurance,
        snapshot_planned_load_minutes = p_snapshot_planned_load_minutes,
        snapshot_planned_unload_minutes = p_snapshot_planned_unload_minutes,
        actual_load_minutes = p_actual_load_minutes,
        actual_unload_minutes = p_actual_unload_minutes,
        snapshot_total_revenue = p_snapshot_total_revenue
    WHERE scenario_id = p_scenario_id;
END $$

DROP PROCEDURE IF EXISTS update_manifest_item $$
CREATE PROCEDURE update_manifest_item(
    IN p_manifest_item_id INT,
    IN p_scenario_id INT,
    IN p_supply_id INT,
    IN p_demand_id INT,
    IN p_quantity_loaded DECIMAL(10,2),
    IN p_snapshot_cost_per_item DECIMAL(10,2),
    IN p_snapshot_items_per_unit INT,
    IN p_snapshot_unit_weight DECIMAL(8,2),
    IN p_snapshot_price_per_item DECIMAL(10,2)
)
BEGIN
    UPDATE manifest_items
    SET
        scenario_id = p_scenario_id,
        supply_id = p_supply_id,
        demand_id = p_demand_id,
        quantity_loaded = p_quantity_loaded,
        snapshot_cost_per_item = p_snapshot_cost_per_item,
        snapshot_items_per_unit = p_snapshot_items_per_unit,
        snapshot_unit_weight = p_snapshot_unit_weight,
        snapshot_price_per_item = p_snapshot_price_per_item
    WHERE manifest_item_id = p_manifest_item_id;
END $$

DELIMITER ;
