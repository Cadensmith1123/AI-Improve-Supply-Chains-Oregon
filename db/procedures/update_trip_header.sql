DELIMITER $$

DROP PROCEDURE IF EXISTS update_trip_header $$

CREATE PROCEDURE update_trip_header(
    IN p_tenant_id INT,
    IN p_scenario_id INT,

    IN p_route_id INT,
    IN p_vehicle_id INT,
    IN p_driver_id INT,
    IN p_run_date DATE,
    IN p_current_gas_price DECIMAL(6,3),
    IN p_total_revenue DECIMAL(12,2)
)
BEGIN
    -- Current values
    DECLARE v_route_id INT;
    DECLARE v_vehicle_id INT;
    DECLARE v_driver_id INT;

    DECLARE v_new_route_id INT;
    DECLARE v_new_vehicle_id INT;
    DECLARE v_new_driver_id INT;

    DECLARE v_driver_wage DECIMAL(5,2);
    DECLARE v_driver_load_wage DECIMAL(5,2);
    DECLARE v_vehicle_mpg DECIMAL(4,1);
    DECLARE v_annual_insurance DECIMAL(10,2);
    DECLARE v_annual_maintenance DECIMAL(10,2);
    DECLARE v_load_time INT;
    DECLARE v_unload_time INT;

    -- Required check
    IF p_scenario_id IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'scenario_id is required';
    END IF;

    -- Load current header ids (and ensure scenario exists)
    SELECT route_id, vehicle_id, driver_id
    INTO v_route_id, v_vehicle_id, v_driver_id
    FROM scenarios
    WHERE scenario_id = p_scenario_id AND tenant_id = p_tenant_id;

    IF v_route_id IS NULL AND v_vehicle_id IS NULL AND v_driver_id IS NULL THEN
        -- This "exists" check is imperfect if all three are NULL in a valid row,
        -- so do a safer check:
        IF (SELECT COUNT(*) FROM scenarios WHERE scenario_id = p_scenario_id AND tenant_id = p_tenant_id) = 0 THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'scenario_id not found';
        END IF;
    END IF;

    -- Decide new ids (NULL means "keep current")
    SET v_new_route_id   = COALESCE(p_route_id,   v_route_id);
    SET v_new_vehicle_id = COALESCE(p_vehicle_id, v_vehicle_id);
    SET v_new_driver_id  = COALESCE(p_driver_id,  v_driver_id);

    /*
      Re-snapshot dependent fields when IDs change.
      If the new id ends up NULL, we fall back to 0s.
    */

    -- Driver snapshot (if driver changed)
    IF v_new_driver_id IS NULL THEN
        SET v_driver_wage = 0.00;
        SET v_driver_load_wage = 0.00;
    ELSEIF v_new_driver_id <> v_driver_id OR v_driver_id IS NULL THEN
        SELECT hourly_drive_wage, hourly_load_wage
        INTO v_driver_wage, v_driver_load_wage
        FROM drivers
        WHERE driver_id = v_new_driver_id AND tenant_id = p_tenant_id;
    ELSE
        -- keep existing snapshot values
        SELECT snapshot_driver_wage, snapshot_driver_load_wage
        INTO v_driver_wage, v_driver_load_wage
        FROM scenarios
        WHERE scenario_id = p_scenario_id AND tenant_id = p_tenant_id;
    END IF;

    -- Vehicle snapshot (if vehicle changed)
    IF v_new_vehicle_id IS NULL THEN
        SET v_vehicle_mpg = 0.0;
        SET v_annual_insurance = 0.00;
        SET v_annual_maintenance = 0.00;
    ELSEIF v_new_vehicle_id <> v_vehicle_id OR v_vehicle_id IS NULL THEN
        SELECT mpg, annual_insurance_cost, annual_maintenance_cost
        INTO v_vehicle_mpg, v_annual_insurance, v_annual_maintenance
        FROM vehicles
        WHERE vehicle_id = v_new_vehicle_id AND tenant_id = p_tenant_id;
    ELSE
        SELECT snapshot_vehicle_mpg, (snapshot_daily_insurance * 365.0), (snapshot_daily_maintenance_cost * 365.0)
        INTO v_vehicle_mpg, v_annual_insurance, v_annual_maintenance
        FROM scenarios
        WHERE scenario_id = p_scenario_id AND tenant_id = p_tenant_id;
    END IF;

    -- Route snapshot times (if route changed)
    IF v_new_route_id IS NULL THEN
        SET v_load_time = 0;
        SET v_unload_time = 0;
    ELSEIF v_new_route_id <> v_route_id OR v_route_id IS NULL THEN
        SELECT l_orig.avg_load_minutes, l_dest.avg_unload_minutes
        INTO v_load_time, v_unload_time
        FROM routes r
        JOIN locations l_orig ON r.origin_location_id = l_orig.location_id AND l_orig.tenant_id = p_tenant_id
        JOIN locations l_dest ON r.dest_location_id = l_dest.location_id AND l_dest.tenant_id = p_tenant_id
        WHERE r.route_id = v_new_route_id AND r.tenant_id = p_tenant_id;
    ELSE
        SELECT snapshot_planned_load_minutes, snapshot_planned_unload_minutes
        INTO v_load_time, v_unload_time
        FROM scenarios
        WHERE scenario_id = p_scenario_id AND tenant_id = p_tenant_id;
    END IF;

    -- Now update the scenario row
    UPDATE scenarios
    SET
        route_id = v_new_route_id,
        vehicle_id = v_new_vehicle_id,
        driver_id = v_new_driver_id,

        run_date = COALESCE(p_run_date, run_date),

        snapshot_driver_wage = COALESCE(v_driver_wage, snapshot_driver_wage),
        snapshot_driver_load_wage = COALESCE(v_driver_load_wage, snapshot_driver_load_wage),

        snapshot_vehicle_mpg = COALESCE(v_vehicle_mpg, snapshot_vehicle_mpg),

        snapshot_gas_price = COALESCE(p_current_gas_price, snapshot_gas_price),

        snapshot_daily_insurance = COALESCE((COALESCE(v_annual_insurance, 0.00) / 365.0), snapshot_daily_insurance),
        snapshot_daily_maintenance_cost = COALESCE((COALESCE(v_annual_maintenance, 0.00) / 365.0), snapshot_daily_maintenance_cost),

        snapshot_planned_load_minutes = COALESCE(v_load_time, snapshot_planned_load_minutes),
        snapshot_planned_unload_minutes = COALESCE(v_unload_time, snapshot_planned_unload_minutes),

        snapshot_total_revenue = COALESCE(p_total_revenue, snapshot_total_revenue)

    WHERE scenario_id = p_scenario_id AND tenant_id = p_tenant_id;

    -- return updated row for convenience
    SELECT * FROM scenarios WHERE scenario_id = p_scenario_id AND tenant_id = p_tenant_id;
END $$

DELIMITER ;
