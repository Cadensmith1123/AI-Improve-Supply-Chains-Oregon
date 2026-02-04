from db.functions.simple_functions import read
from db.functions.connect import get_db


def get_locations():
    location_data = read.view_locations(columns=['location_id', 'name'])
    return location_data