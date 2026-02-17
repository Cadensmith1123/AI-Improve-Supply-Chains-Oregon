DROP DATABASE IF EXISTS local_food_db;
CREATE DATABASE local_food_db;
USE local_food_db;

-- 1. Locations
CREATE TABLE locations (
    tenant_id INT NOT NULL,
    location_id INT NOT NULL AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    type ENUM('Hub', 'Store', 'Farm') NOT NULL,
    address_street VARCHAR(255),
    city VARCHAR(100),
    state VARCHAR(50),
    zip_code VARCHAR(20),
    phone VARCHAR(20),
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    avg_load_minutes INT DEFAULT 30,
    avg_unload_minutes INT DEFAULT 30,
    
    PRIMARY KEY (tenant_id, location_id),
    KEY (location_id) -- Required for AUTO_INCREMENT
);

-- 2. Products Master
CREATE TABLE products_master (
    tenant_id INT NOT NULL,
    product_code VARCHAR(50) NOT NULL,
    name VARCHAR(100) NOT NULL,
    storage_type ENUM('Dry', 'Ref', 'Frz') NOT NULL,

    PRIMARY KEY (tenant_id, product_code)
);

-- 3. Drivers
CREATE TABLE drivers (
    tenant_id INT NOT NULL,
    driver_id INT NOT NULL AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    hourly_drive_wage DECIMAL(5, 2) NOT NULL,
    hourly_load_wage DECIMAL(5, 2) NOT NULL,

    PRIMARY KEY (tenant_id, driver_id),
    KEY (driver_id)
);

-- 4. Vehicles
CREATE TABLE vehicles (
    tenant_id INT NOT NULL,
    vehicle_id INT NOT NULL AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    mpg DECIMAL(4, 1) NOT NULL,
    depreciation_per_mile DECIMAL(5, 3) DEFAULT 0.000,
    annual_insurance_cost DECIMAL(10, 2) DEFAULT 0.00,
    annual_maintenance_cost DECIMAL(10, 2) DEFAULT 0.00,
    max_weight_lbs DECIMAL(10, 2) NOT NULL,
    max_volume_cubic_ft DECIMAL(10, 2) NOT NULL,
    storage_type ENUM('Dry', 'Ref', 'Frz', 'Multi') NOT NULL,

    PRIMARY KEY (tenant_id, vehicle_id),
    KEY (vehicle_id)
);

-- 5. Entities (Owners of supply)
CREATE TABLE entities (
    tenant_id INT NOT NULL,
    entity_id INT NOT NULL AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    entity_min_profit DECIMAL(10, 2) DEFAULT 0.00,

    PRIMARY KEY (tenant_id, entity_id),
    KEY (entity_id)
);

-- 6. Supply
CREATE TABLE supply (
    tenant_id INT NOT NULL,
    supply_id INT NOT NULL AUTO_INCREMENT,
    entity_id INT NOT NULL,
    location_id INT NOT NULL,
    product_code VARCHAR(50) NOT NULL,
    quantity_available DECIMAL(10, 2) NOT NULL,
    unit_weight_lbs DECIMAL(10, 2) DEFAULT 0.00,
    unit_volume_cu_ft DECIMAL(10, 2) DEFAULT 0.00,
    items_per_handling_unit INT DEFAULT 1,
    cost_per_item DECIMAL(10, 2) DEFAULT 0.00,

    PRIMARY KEY (tenant_id, supply_id),
    KEY (supply_id),
    FOREIGN KEY (tenant_id, entity_id) REFERENCES entities(tenant_id, entity_id),
    FOREIGN KEY (tenant_id, location_id) REFERENCES locations(tenant_id, location_id),
    FOREIGN KEY (tenant_id, product_code) REFERENCES products_master(tenant_id, product_code)
);

-- 7. Demand
CREATE TABLE demand (
    tenant_id INT NOT NULL,
    demand_id INT NOT NULL AUTO_INCREMENT,
    location_id INT NOT NULL,
    product_code VARCHAR(50) NOT NULL,
    quantity_needed DECIMAL(10, 2) NOT NULL,
    max_price DECIMAL(10, 2) DEFAULT 0.00,

    PRIMARY KEY (tenant_id, demand_id),
    KEY (demand_id),
    FOREIGN KEY (tenant_id, location_id) REFERENCES locations(tenant_id, location_id),
    FOREIGN KEY (tenant_id, product_code) REFERENCES products_master(tenant_id, product_code)
);

-- 8. Routes
CREATE TABLE routes (
    tenant_id INT NOT NULL,
    route_id INT NOT NULL AUTO_INCREMENT,
    name VARCHAR(100),
    origin_location_id INT NOT NULL,
    dest_location_id INT NOT NULL,

    PRIMARY KEY (tenant_id, route_id),
    KEY (route_id),
    FOREIGN KEY (tenant_id, origin_location_id) REFERENCES locations(tenant_id, location_id),
    FOREIGN KEY (tenant_id, dest_location_id) REFERENCES locations(tenant_id, location_id)
);

-- 9. Scenarios (Trip Headers)
CREATE TABLE scenarios (
    tenant_id INT NOT NULL,
    scenario_id INT NOT NULL AUTO_INCREMENT,
    route_id INT NOT NULL,
    vehicle_id INT,
    driver_id INT,
    run_date DATE,
    
    -- Snapshots
    snapshot_driver_wage DECIMAL(5, 2),
    snapshot_driver_load_wage DECIMAL(5, 2),
    snapshot_vehicle_mpg DECIMAL(4, 1),
    snapshot_gas_price DECIMAL(6, 3),
    snapshot_daily_insurance DECIMAL(10, 2),
    snapshot_daily_maintenance_cost DECIMAL(10, 2),
    snapshot_planned_load_minutes INT,
    snapshot_planned_unload_minutes INT,
    
    actual_load_minutes INT DEFAULT 0,
    actual_unload_minutes INT DEFAULT 0,
    snapshot_total_revenue DECIMAL(12, 2) DEFAULT 0.00,

    PRIMARY KEY (tenant_id, scenario_id),
    KEY (scenario_id),
    FOREIGN KEY (tenant_id, route_id) REFERENCES routes(tenant_id, route_id),
    FOREIGN KEY (tenant_id, vehicle_id) REFERENCES vehicles(tenant_id, vehicle_id),
    FOREIGN KEY (tenant_id, driver_id) REFERENCES drivers(tenant_id, driver_id)
);

-- 10. Manifest Items (Trip Lines)
CREATE TABLE manifest_items (
    tenant_id INT NOT NULL,
    manifest_item_id INT NOT NULL AUTO_INCREMENT,
    scenario_id INT NOT NULL,
    supply_id INT,
    demand_id INT,
    
    item_name VARCHAR(100),
    quantity_loaded DECIMAL(10, 2),
    
    -- Snapshots
    snapshot_cost_per_item DECIMAL(10, 2),
    snapshot_items_per_unit INT,
    snapshot_unit_weight DECIMAL(10, 2),
    snapshot_unit_volume DECIMAL(10, 2),
    snapshot_price_per_item DECIMAL(10, 2),

    PRIMARY KEY (tenant_id, manifest_item_id),
    KEY (manifest_item_id),
    FOREIGN KEY (tenant_id, scenario_id) REFERENCES scenarios(tenant_id, scenario_id) ON DELETE CASCADE,
    FOREIGN KEY (tenant_id, supply_id) REFERENCES supply(tenant_id, supply_id),
    FOREIGN KEY (tenant_id, demand_id) REFERENCES demand(tenant_id, demand_id)
);

-- 11. Triggers for Inventory Management
DELIMITER $$

CREATE TRIGGER trg_manifest_insert AFTER INSERT ON manifest_items
FOR EACH ROW
BEGIN
    -- Update Supply
    IF NEW.supply_id IS NOT NULL AND NEW.supply_id != 0 THEN
        UPDATE supply 
        SET quantity_available = quantity_available - NEW.quantity_loaded
        WHERE supply_id = NEW.supply_id AND tenant_id = NEW.tenant_id;
    END IF;

    -- Update Demand
    IF NEW.demand_id IS NOT NULL AND NEW.supply_id != 0 THEN
        UPDATE demand 
        SET quantity_needed = quantity_needed - NEW.quantity_loaded
        WHERE demand_id = NEW.demand_id AND tenant_id = NEW.tenant_id;
    END IF;
END $$

CREATE TRIGGER trg_manifest_update AFTER UPDATE ON manifest_items
FOR EACH ROW
BEGIN
    -- Revert Old Supply
    IF OLD.supply_id IS NOT NULL AND NEW.demand_id != 0 THEN
        UPDATE supply 
        SET quantity_available = quantity_available + OLD.quantity_loaded
        WHERE supply_id = OLD.supply_id AND tenant_id = OLD.tenant_id;
    END IF;
    -- Apply New Supply
    IF NEW.supply_id IS NOT NULL AND NEW.demand_id != 0 THEN
        UPDATE supply 
        SET quantity_available = quantity_available - NEW.quantity_loaded
        WHERE supply_id = NEW.supply_id AND tenant_id = NEW.tenant_id;
    END IF;

    -- Revert Old Demand
    IF OLD.demand_id IS NOT NULL AND NEW.demand_id != 0 THEN
        UPDATE demand 
        SET quantity_needed = quantity_needed + OLD.quantity_loaded
        WHERE demand_id = OLD.demand_id AND tenant_id = OLD.tenant_id;
    END IF;
    -- Apply New Demand
    IF NEW.demand_id IS NOT NULL AND NEW.demand_id != 0 THEN
        UPDATE demand 
        SET quantity_needed = quantity_needed - NEW.quantity_loaded
        WHERE demand_id = NEW.demand_id AND tenant_id = NEW.tenant_id;
    END IF;
END $$

CREATE TRIGGER trg_manifest_delete AFTER DELETE ON manifest_items
FOR EACH ROW
BEGIN
    -- Restore Supply
    IF OLD.supply_id IS NOT NULL THEN
        UPDATE supply 
        SET quantity_available = quantity_available + OLD.quantity_loaded
        WHERE supply_id = OLD.supply_id AND tenant_id = OLD.tenant_id;
    END IF;

    -- Restore Demand
    IF OLD.demand_id IS NOT NULL THEN
        UPDATE demand 
        SET quantity_needed = quantity_needed + OLD.quantity_loaded
        WHERE demand_id = OLD.demand_id AND tenant_id = OLD.tenant_id;
    END IF;
END $$

DELIMITER ;