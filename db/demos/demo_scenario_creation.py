#import pytest
from db.functions import scenario_management
from db.functions.simple_functions import delete, create, read
from dotenv import load_dotenv
import os
import mysql.connector

load_dotenv()


def connect_db():
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
    except Exception:
        return None


def test_scenario_creation_with_manifest(output_file, connection = None):
    scen_id = scenario_management.create_scenario(1, "2000.53", conn=connection)

    manifest_args = [
        {
            'scenario_id':scen_id,
            "item_name": "apples",
            "quantity_loaded": 1,
            "cost_per_item": .7,
            "unit_weight": 42,
            "unit_volume": 1.244,
            
            "items_per_unit": 100,
            "price_per_item": 2
        },
        {
            'scenario_id': scen_id,
            "item_name": "pears",
            "quantity_loaded": 2,
            "cost_per_item": .5,
            "unit_weight": 45,
            "unit_volume": 1.244,
            "items_per_unit": 140,
            "price_per_item": 3
        }
    ]
    scenario_management.add_manifest_items(**manifest_args[0], conn=connection)
    
    scenario_management.add_manifest_items(**manifest_args[1], conn=connection)

    trip_details = scenario_management.get_trip_details(scen_id, conn=connection)
    print(trip_details)
    scenario_management.export_trip_csv(trip_details, output_file)
    return  trip_details, scen_id



def test_edit_scenario(scen_id, connection=None):
    scenario_management.update_scenario(scenario_id=scen_id, vehicle_id=1, driver_id=1, current_gas_price=4.00, total_revenue=2000.84, conn=connection)


trip_details, scen_id = test_scenario_creation_with_manifest("test.csv", connection = connect_db())
test_edit_scenario(scen_id, connection=connect_db())
trip_details = scenario_management.get_trip_details(scen_id, conn=connect_db())
scenario_management.export_trip_csv(trip_details, "test2.csv")