-- =============================================
-- LOCAL FOOD OPTIMIZATION SCHEMA
-- Database Name: local_food_db
-- =============================================

DROP SCHEMA IF EXISTS local_food_db;
CREATE SCHEMA local_food_db;
USE local_food_db;

SET FOREIGN_KEY_CHECKS = 0;

-- =============================================
-- 1. INFRASTRUCTURE & MASTER DATA
-- =============================================
CREATE TABLE locations (
    location_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL, 
    type ENUM('Hub', 'Store', 'Farm') DEFAULT 'Hub',
    
    address_street VARCHAR(255),
    city VARCHAR(100),
    state VARCHAR(50), 
    zip VARCHAR(20),   
    phone VARCHAR(20), 
    
    latitude DECIMAL(9,6),  
    longitude DECIMAL(9,6),
    
    avg_load_minutes INT DEFAULT 30,
    avg_unload_minutes INT DEFAULT 30
);

CREATE TABLE products_master (
    product_code VARCHAR(50) PRIMARY KEY, 
    name VARCHAR(100) NOT NULL,
    storage_type ENUM('Dry', 'Ref', 'Frz') NOT NULL
);

-- =============================================
-- 2. ASSETS
-- =============================================
CREATE TABLE drivers (
    driver_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    hourly_drive_wage DECIMAL(5,2) NOT NULL,
    hourly_load_wage DECIMAL(5,2) NOT NULL
);

CREATE TABLE vehicles (
    vehicle_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    
    mpg DECIMAL(4,1) NOT NULL,
    depreciation_per_mile DECIMAL(10,2) NOT NULL,
    
    annual_insurance_cost DECIMAL(10,2) NOT NULL DEFAULT 0.00,

    max_weight_lbs INT NOT NULL,
    max_volume_cubic_ft INT NOT NULL,
    storage_capability ENUM('Dry', 'Ref', 'Frz', 'Multi') NOT NULL
);

-- =============================================
-- 3. BUSINESS ENTITIES
-- =============================================
CREATE TABLE entities (
    entity_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    
    entity_min_profit INT DEFAULT 0
);

-- =============================================
-- 4. SUPPLY
-- =============================================
CREATE TABLE supply (
    supply_id INT AUTO_INCREMENT PRIMARY KEY,
    entity_id INT NOT NULL,
    location_id INT NOT NULL,
    product_code VARCHAR(50) NOT NULL,
    
    -- LOGISTICS UNIT
    quantity_available DECIMAL(10,2) NOT NULL, -- e.g. "5" (crates)
    
    -- PER HANDLING UNIT INFO
    unit_weight_lbs DECIMAL(8,2) NOT NULL,     -- e.g. crate weighs 50 lbs
    unit_volume_cu_ft DECIMAL(8,2) NOT NULL,   -- e.g. crate is 5 cubic feet
    
    -- PER SALE UNIT INFO
    items_per_handling_unit INT NOT NULL DEFAULT 1, -- e.g. 48 (Cases inside)
    cost_per_item DECIMAL(10,2) NOT NULL,           -- e.g. $20 (per Case cost to manufacture/for hub)

    FOREIGN KEY (entity_id) REFERENCES entities(entity_id) ON DELETE RESTRICT,
    FOREIGN KEY (location_id) REFERENCES locations(location_id) ON DELETE RESTRICT,
    FOREIGN KEY (product_code) REFERENCES products_master(product_code) ON DELETE RESTRICT
);

-- =============================================
-- 5. DEMAND
-- =============================================
CREATE TABLE demand (
    demand_id INT AUTO_INCREMENT PRIMARY KEY,
    location_id INT NOT NULL, 
    product_code VARCHAR(50) NOT NULL,
    
    quantity_needed DECIMAL(10,2) NOT NULL,
    max_price DECIMAL(10,2) NOT NULL, 
    
    FOREIGN KEY (location_id) REFERENCES locations(location_id) ON DELETE CASCADE,
    FOREIGN KEY (product_code) REFERENCES products_master(product_code) ON DELETE CASCADE
);

-- =============================================
-- 6. OPERATIONS & SNAPSHOTS
-- =============================================
CREATE TABLE routes (
    route_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100),
    origin_location_id INT NOT NULL,
    dest_location_id INT NOT NULL,
    FOREIGN KEY (origin_location_id) REFERENCES locations(location_id) ON DELETE RESTRICT,
    FOREIGN KEY (dest_location_id) REFERENCES locations(location_id) ON DELETE RESTRICT
);

CREATE TABLE scenarios (
    scenario_id INT AUTO_INCREMENT PRIMARY KEY,
    route_id INT,        
    vehicle_id INT,
    driver_id INT,
    run_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    snapshot_driver_wage DECIMAL(5,2) NOT NULL,
    snapshot_driver_load_wage DECIMAL(5,2) NOT NULL,
    snapshot_vehicle_mpg DECIMAL(4,1) NOT NULL,
    snapshot_gas_price DECIMAL(4,2) NOT NULL,
    snapshot_daily_insurance DECIMAL(10,2) NOT NULL, 
    
    snapshot_planned_load_minutes INT NOT NULL,
    snapshot_planned_unload_minutes INT NOT NULL,

    actual_load_minutes INT DEFAULT NULL,
    actual_unload_minutes INT DEFAULT NULL,
    
    FOREIGN KEY (route_id) REFERENCES routes(route_id) ON DELETE SET NULL,
    FOREIGN KEY (vehicle_id) REFERENCES vehicles(vehicle_id) ON DELETE SET NULL,
    FOREIGN KEY (driver_id) REFERENCES drivers(driver_id) ON DELETE SET NULL
);

CREATE TABLE manifest_items (
    manifest_item_id INT AUTO_INCREMENT PRIMARY KEY,
    scenario_id INT NOT NULL,
    supply_id INT NOT NULL,
    demand_id INT, 
    
    quantity_loaded DECIMAL(10,2) NOT NULL,
    
    snapshot_cost_per_item DECIMAL(10,2) NOT NULL,
    snapshot_items_per_unit INT NOT NULL, 
    snapshot_unit_weight DECIMAL(8,2) NOT NULL,
    snapshot_price_per_item DECIMAL(10,2) NOT NULL,
    
    FOREIGN KEY (scenario_id) REFERENCES scenarios(scenario_id) ON DELETE CASCADE,
    FOREIGN KEY (supply_id) REFERENCES supply(supply_id) ON DELETE RESTRICT,
    FOREIGN KEY (demand_id) REFERENCES demand(demand_id) ON DELETE SET NULL
);

-- =============================================
-- 7. TRIGGERS
-- =============================================
DELIMITER $$

CREATE TRIGGER trg_manifest_insert
AFTER INSERT ON manifest_items FOR EACH ROW
BEGIN
    UPDATE supply SET quantity_available = quantity_available - NEW.quantity_loaded
    WHERE supply_id = NEW.supply_id;
END$$

CREATE TRIGGER trg_manifest_delete
AFTER DELETE ON manifest_items FOR EACH ROW
BEGIN
    UPDATE supply SET quantity_available = quantity_available + OLD.quantity_loaded
    WHERE supply_id = OLD.supply_id;
END$$

DELIMITER ;

SET FOREIGN_KEY_CHECKS = 1;