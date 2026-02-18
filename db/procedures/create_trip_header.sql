DELIMITER $$

DROP PROCEDURE IF EXISTS create_trip_header $$

CREATE PROCEDURE create_trip_header(
    IN p_tenant_id INT,
    IN p_route_id INT,
    IN p_vehicle_id INT,
    IN p_driver_id INT,
    IN p_run_date DATE,
    IN p_current_gas_price DECIMAL(6,3),
    IN p_total_revenue DECIMAL(12,2),
    OUT p_new_scenario_id INT -- Returns ID so Python can add items
)
BEGIN
    DECLARE v_driver_wage DECIMAL(5,2);
    DECLARE v_driver_load_wage DECIMAL(5,2);
    DECLARE v_vehicle_mpg DECIMAL(4,1);
    DECLARE v_annual_insurance DECIMAL(10,2);
    DECLARE v_annual_maintenance DECIMAL(10,2);
    DECLARE v_load_time INT;
    DECLARE v_unload_time INT;

    -- 1. Get Driver Snapshot
    IF p_driver_id IS NOT NULL THEN
        SELECT hourly_drive_wage, hourly_load_wage
        INTO v_driver_wage, v_driver_load_wage
        FROM drivers WHERE driver_id = p_driver_id AND tenant_id = p_tenant_id;
    END IF;

    -- 2. Get Vehicle Snapshot
    IF p_vehicle_id IS NOT NULL THEN
        SELECT mpg, annual_insurance_cost, annual_maintenance_cost
        INTO v_vehicle_mpg, v_annual_insurance, v_annual_maintenance
        FROM vehicles WHERE vehicle_id = p_vehicle_id AND tenant_id = p_tenant_id;
    END IF;

    -- 3. Get Route Snapshot
    IF p_route_id IS NOT NULL THEN
        SELECT l_orig.avg_load_minutes, l_dest.avg_unload_minutes
        INTO v_load_time, v_unload_time
        FROM routes r
        JOIN locations l_orig ON r.origin_location_id = l_orig.location_id AND l_orig.tenant_id = p_tenant_id
        JOIN locations l_dest ON r.dest_location_id = l_dest.location_id AND l_dest.tenant_id = p_tenant_id
        WHERE r.route_id = p_route_id AND r.tenant_id = p_tenant_id;
    END IF;

    -- 4. Insert
    INSERT INTO scenarios (
        tenant_id,
        route_id, vehicle_id, driver_id, run_date,
        snapshot_driver_wage, snapshot_driver_load_wage,
        snapshot_vehicle_mpg, snapshot_gas_price,
        snapshot_daily_insurance, snapshot_daily_maintenance_cost,
        snapshot_planned_load_minutes, snapshot_planned_unload_minutes,
        snapshot_total_revenue
    )
    VALUES (
        p_tenant_id,
        p_route_id, p_vehicle_id, p_driver_id, p_run_date,
        v_driver_wage, v_driver_load_wage,
        v_vehicle_mpg, p_current_gas_price,
        (v_annual_insurance / 365.0), (v_annual_maintenance / 365.0),
        v_load_time, v_unload_time,
        p_total_revenue
    );

    SET p_new_scenario_id = LAST_INSERT_ID();
END $$

DELIMITER ;