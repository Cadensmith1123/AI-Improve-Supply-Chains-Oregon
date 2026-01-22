DELIMITER $$

DROP PROCEDURE IF EXISTS create_trip_header$$

CREATE PROCEDURE create_trip_header(
    IN p_route_id INT,
    IN p_vehicle_id INT,
    IN p_driver_id INT,
    IN p_run_date DATE,
    IN p_current_gas_price DECIMAL(4,2),
    OUT p_new_scenario_id INT -- Returns ID so Python can add items
)
BEGIN
    DECLARE v_driver_wage DECIMAL(5,2);
    DECLARE v_driver_load_wage DECIMAL(5,2);
    DECLARE v_vehicle_mpg DECIMAL(4,1);
    DECLARE v_annual_insurance DECIMAL(10,2);
    DECLARE v_load_time INT;
    DECLARE v_unload_time INT;

    -- 1. Snapshot Rates
    SELECT hourly_drive_wage, hourly_load_wage 
    INTO v_driver_wage, v_driver_load_wage 
    FROM drivers WHERE driver_id = p_driver_id;

    SELECT mpg, annual_insurance_cost 
    INTO v_vehicle_mpg, v_annual_insurance 
    FROM vehicles WHERE vehicle_id = p_vehicle_id;

    -- 2. Snapshot Time Estimates (From Locations)
    SELECT l_orig.avg_load_minutes, l_dest.avg_unload_minutes
    INTO v_load_time, v_unload_time
    FROM routes r
    JOIN locations l_orig ON r.origin_location_id = l_orig.location_id
    JOIN locations l_dest ON r.dest_location_id = l_dest.location_id
    WHERE r.route_id = p_route_id;

    -- 3. Create Scenario Record
    INSERT INTO scenarios (
        route_id, vehicle_id, driver_id, run_date,
        snapshot_driver_wage, snapshot_driver_load_wage,
        snapshot_vehicle_mpg, snapshot_gas_price, snapshot_daily_insurance,
        snapshot_planned_load_minutes, snapshot_planned_unload_minutes
    ) VALUES (
        p_route_id, p_vehicle_id, p_driver_id, p_run_date,
        v_driver_wage, v_driver_load_wage,
        v_vehicle_mpg, p_current_gas_price, (v_annual_insurance / 365.0),
        v_load_time, v_unload_time
    );

    SET p_new_scenario_id = LAST_INSERT_ID();
END$$