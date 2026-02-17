from db.functions import scenario_management
from db.functions.simple_functions import delete, create, read
from dotenv import load_dotenv
import os
import mysql.connector

load_dotenv()


def connect_test_db():
    try:
        config = {
            'user': os.getenv("DB_USER"),
            'password': os.getenv("DB_PASSWORD"),
            'host': os.getenv("DB_HOST"),
            'port': os.getenv("DB_PORT"),
            'database': 'test_db',
            'connection_timeout': 10
        }
        return mysql.connector.connect(**config)
    except Exception as e:
        print(f"Connection failed: {e}")
        return None


def test_scenario_creation_with_manifest(route_id, output_file, conn=None):
    manifest_args = [
        {
            'tenant_id': 1,
            "item_name": "apples",
            "quantity_loaded": 1,
            "cost_per_item": .7,
            "unit_weight_lbs": 42,
            "unit_volume": 1.244,
            
            "items_per_unit": 100,
            "price_per_item": 2
        },
        {
            'tenant_id': 1,
            "item_name": "pears",
            "quantity_loaded": 2,
            "cost_per_item": .5,
            "unit_weight_lbs": 45,
            "unit_volume": 1.244,
            "items_per_unit": 140,
            "price_per_item": 3
        }
    ]

    # 1. Preview Metrics
    print("\n--- PREVIEW (No DB Save) ---")
    preview = scenario_management.calculate_scenario_metrics(manifest_args, entered_revenue=2000.53)
    print(f"Preview Calculated Revenue: {preview['totals']['calculated_revenue']}")
    print(f"Preview Total Weight: {preview['totals']['total_weight_lbs']}")

    # 2. Save to DB
    print("\n--- SAVING TO DB ---")
    scen_id = scenario_management.create_scenario(1, route_id, 2000.53, conn=conn)
    
    # Inject scenario_id and map keys for saving
    for item in manifest_args:
        item['scenario_id'] = scen_id
        scenario_management.add_manifest_items(**item, conn=conn)

    # 3. Fetch from DB (Verify logic matches)
    trip_details = scenario_management.get_trip_details(1, scen_id, conn=conn)
    print(trip_details)
    scenario_management.export_trip_csv(trip_details, output_file)
    return  trip_details, scen_id



def test_edit_scenario(scen_id, driver_id, vehicle_id, conn=None):
    scenario_management.update_scenario(
        tenant_id=1,
        scenario_id=scen_id, 
        vehicle_id=vehicle_id, 
        driver_id=driver_id, 
        current_gas_price=4.00, 
        total_revenue=2000.84,
        conn=conn
    )


if __name__ == "__main__":
    conn = connect_test_db()
    if not conn:
        exit("Failed to connect to test database.")

    tenant_id = 1
    loc1_id = None
    loc2_id = None
    route_id = None
    driver_id = None
    vehicle_id = None
    scen_id = None

    try:
        print("Setting up dependencies")
        loc1_id = create.add_location(tenant_id, "Demo Hub", "Hub", "123 St", "City", "OR", "97000", "555-1212", 0, 0, 20, 20, conn=conn)
        loc2_id = create.add_location(tenant_id, "Demo Store", "Store", "456 Ave", "City", "OR", "97000", "555-1313", 0, 0, 30, 30, conn=conn)
        route_id = create.add_route(tenant_id, "Demo Route", loc1_id, loc2_id, conn=conn)
        driver_id = create.add_driver(tenant_id, "Demo Driver", 25.00, 15.00, conn=conn)
        vehicle_id = create.add_vehicle(tenant_id, "Demo Truck", 10.0, 0.5, 1000, 500, 10000, 1000, "Dry", conn=conn)

        print("Running Scenario Demo")
        trip_details, scen_id = test_scenario_creation_with_manifest(route_id, "test.csv", conn=conn)
        
        print("Running Edit Demo")
        test_edit_scenario(scen_id, driver_id, vehicle_id, conn=conn)
        
        print("Fetching final details")
        trip_details = scenario_management.get_trip_details(tenant_id, scen_id, conn=conn)
        scenario_management.export_trip_csv(trip_details, "test2.csv")
        print("Demo complete. Check test.csv and test2.csv.")

    finally:
        print("Cleaning up")
        if scen_id: delete.delete_plan(tenant_id, scen_id, conn=conn)
        if route_id: delete.delete_route(tenant_id, route_id, conn=conn)
        if vehicle_id: delete.delete_vehicle(tenant_id, vehicle_id, conn=conn)
        if driver_id: delete.delete_driver(tenant_id, driver_id, conn=conn)
        if loc1_id: delete.delete_location(tenant_id, loc1_id, conn=conn)
        if loc2_id: delete.delete_location(tenant_id, loc2_id, conn=conn)
        print("Cleanup complete.")
        if conn:
            conn.close()