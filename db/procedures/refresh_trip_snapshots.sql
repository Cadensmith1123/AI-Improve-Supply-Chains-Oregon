DELIMITER $$

DROP PROCEDURE IF EXISTS refresh_trip_snapshots $$

CREATE PROCEDURE refresh_trip_snapshots(
    IN p_tenant_id INT,
    IN p_scenario_id INT,
    IN p_depreciation DECIMAL(5,3)
)
BEGIN
    -- Update Driver Snapshots
    UPDATE scenarios s
    JOIN drivers d ON s.driver_id = d.driver_id AND s.tenant_id = d.tenant_id
    SET 
        s.snapshot_driver_wage = d.hourly_drive_wage,
        s.snapshot_driver_load_wage = d.hourly_load_wage
    WHERE s.scenario_id = p_scenario_id AND s.tenant_id = p_tenant_id;

    -- Update Vehicle Snapshots
    UPDATE scenarios s
    JOIN vehicles v ON s.vehicle_id = v.vehicle_id AND s.tenant_id = v.tenant_id
    SET 
        s.snapshot_vehicle_mpg = v.mpg,
        s.snapshot_daily_insurance = (v.annual_insurance_cost / 365.0),
        s.snapshot_daily_maintenance_cost = (v.annual_maintenance_cost / 365.0),
        s.snapshot_depreciation_per_mile = p_depreciation
    WHERE s.scenario_id = p_scenario_id AND s.tenant_id = p_tenant_id;

    -- Update Route Times (Load/Unload)
    UPDATE scenarios s
    JOIN routes r ON s.route_id = r.route_id AND s.tenant_id = r.tenant_id
    JOIN locations l_orig ON r.origin_location_id = l_orig.location_id
    JOIN locations l_dest ON r.dest_location_id = l_dest.location_id
    SET
        s.snapshot_planned_load_minutes = l_orig.avg_load_minutes,
        s.snapshot_planned_unload_minutes = l_dest.avg_unload_minutes
    WHERE s.scenario_id = p_scenario_id AND s.tenant_id = p_tenant_id;
END $$

DELIMITER ;