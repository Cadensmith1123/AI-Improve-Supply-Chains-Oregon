import read_multiple
from connect import get_db


def get_locations():
    location_data = read_multiple.view_locations(columns=['location_id', 'name'])
    return location_data

print(get_locations())
