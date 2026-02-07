#import pytest
from db.functions import scenario_management
from db.functions.simple_functions import delete, create, read


def test_scenario_creation_with_manifest(output_file):
    scen_id = scenario_management.create_scenario(1, "2000.53")

    manifest_args = [
        {
            'scenario_id':scen_id,
            "item_name": "apples",
            "quantity_loaded": 1,
            "items_per_unit": 500,
            "price_per_item": 2
        },
        {
            'scenario_id': scen_id,
            "item_name": "pears",
            "quantity_loaded": 2,
            "items_per_unit": 50,
            "price_per_item": 10
        }
    ]
    scenario_management.add_manifest_items(**manifest_args[0])
    
    scenario_management.add_manifest_items(**manifest_args[1])

    trip_details = scenario_management.get_trip_details(scen_id)
    print(trip_details)
    scenario_management.export_trip_csv(scen_id, output_file)
    return  scen_id



def test_edit_scenario(scen_id):
    scenario_management.update_scenario(scenario_id=scen_id, vehicle_id=1, driver_id=1, current_gas_price=4.00, total_revenue=2000.84)

scen_id = test_scenario_creation_with_manifest("test.csv")
test_edit_scenario(scen_id)
scenario_management.export_trip_csv(scen_id, "test2.csv")