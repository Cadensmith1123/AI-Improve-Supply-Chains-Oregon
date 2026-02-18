import pytest
import os
import mysql.connector
import dotenv
import re
import db.functions.simple_functions.read as read
import db.functions.simple_functions.create as create
import db.functions.simple_functions.delete as delete
import random
import string

dotenv.load_dotenv()


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
        # Create new test DB
        connection = mysql.connector.connect(**config)

        return connection
    except Exception as e:
        print(f"DB Error: {e}")
        return None


@pytest.fixture(scope="session")
def connection():
    conn = connect_db()
    yield conn
    if conn:
        conn.close()


def parse_schema_features(sql_file_path):
    """
    Parses a SQL file to extract table names and their column names.
    Returns a dictionary: { 'table_name': ['col1', 'col2', ...] }
    """
    schema_dict = {}

    with open(sql_file_path, 'r') as f:
        sql_content = f.read()

    # Find all CREATE TABLE blocks
    table_pattern = re.compile(r"CREATE\s+TABLE\s+(\w+)\s*\((.*?)\);", re.DOTALL | re.IGNORECASE)

    tables = table_pattern.findall(sql_content)

    for table_name, body in tables:
        columns = []

        # Split the body into individual lines/statements
        lines = [line.strip() for line in body.split('\n')]

        for line in lines:
            # Skip empty lines or comments
            if not line or line.startswith('--'):
                continue

            # Filter out Table-Level Constraints
            upper_line = line.upper()
            if upper_line.startswith(('FOREIGN KEY', 'PRIMARY KEY', 'KEY', 'UNIQUE', 'CONSTRAINT', 'INDEX', 'CHECK')):
                continue

            # Extract the Column Name
            parts = line.split()
            if parts:
                col_name = parts[0].strip('`"[],')
                columns.append(col_name)

        schema_dict[table_name] = columns

    return schema_dict


def parse_schema_types(sql_file_path):
    """
    Parses SQL file to extract {table_name: {column_name: column_type_string}}
    Example: {'locations': {'name': 'VARCHAR(100)', 'type': "ENUM('Hub','Store')"}}
    """
    schema_types = {}

    with open(sql_file_path, 'r') as f:
        sql_content = f.read()

    # Find CREATE TABLE blocks
    table_pattern = re.compile(r"CREATE\s+TABLE\s+(\w+)\s*\((.*?)\);", re.DOTALL | re.IGNORECASE)
    tables = table_pattern.findall(sql_content)

    for table_name, body in tables:
        col_types = {}
        lines = [line.strip() for line in body.split('\n')]

        for line in lines:
            if not line or line.startswith('--'): continue
            if line.upper().startswith(('FOREIGN KEY', 'PRIMARY KEY', 'KEY', 'UNIQUE', 'CONSTRAINT', 'INDEX', 'CHECK')):
                continue

            # Extract Column Name and Type
            match = re.match(r"^\s*(`?\w+`?)\s+([A-Z]+(?:\(.*?\))?)", line, re.IGNORECASE)
            if match:
                col_name = match.group(1).strip('`')
                col_type = match.group(2)
                col_types[col_name] = col_type

        schema_types[table_name] = col_types

    return schema_types


def generate_random_value(sql_type):
    """Generates a random Python value based on a SQL type string."""

    # Handle ENUMs (e.g., "ENUM('Hub', 'Store', 'Farm')")
    if "ENUM" in sql_type:
        # Extract options between parens
        options_str = re.search(r"\((.*?)\)", sql_type).group(1)
        options = [opt.strip("' ") for opt in options_str.split(',')]
        return random.choice(options)

    # Handle VARCHAR / CHAR (e.g., "VARCHAR(100)")
    elif "CHAR" in sql_type:
        # Extract length if present, else default to 10
        length_match = re.search(r"\((\d+)\)", sql_type)
        length = int(length_match.group(1)) if length_match else 10
        # Generate random string
        return ''.join(random.choices(string.ascii_letters, k=min(length, 10))) # cap at 10 chars for readability

    # Handle INT
    elif "INT" in sql_type:
        return random.randint(1, 100)

    # Handle DECIMAL / FLOAT
    elif "DECIMAL" in sql_type or "FLOAT" in sql_type:
        return round(random.uniform(10.0, 99.9), 2)

    # Handle DATE
    elif "DATE" in sql_type:
        return f"2025-{random.randint(1,12):02d}-{random.randint(1,28):02d}"

    # Fallback
    return None

@pytest.fixture(scope="session")
def features_dict():
    return parse_schema_features("db/schema/SCHEMA.sql")

@pytest.fixture(scope="session")
def schema_types():
    return parse_schema_types("db/schema/SCHEMA.sql")


def test_01_locations(connection, features_dict, schema_types):
    cols = schema_types['locations']
    
    # 1. Create
    new_id = create.add_location(
            tenant_id=1,
            name=generate_random_value(cols['name']),
            type=generate_random_value(cols['type']),
            address_street=generate_random_value(cols['address_street']),
            city=generate_random_value(cols['city']),
            state=generate_random_value(cols['state']),
            zip_code=generate_random_value(cols['zip_code']),
            phone=generate_random_value(cols['phone']),
            latitude=generate_random_value(cols['latitude']),
            longitude=generate_random_value(cols['longitude']),
            avg_load_minutes=generate_random_value(cols['avg_load_minutes']),
            avg_unload_minutes=generate_random_value(cols['avg_unload_minutes']),
            conn=connection
        )
    print(f"Created Location ID: {new_id}")
    connection.commit()

    # 2. Verify Single Row
    rows = read.view_locations(1, connection, ids=new_id)
    assert len(rows) == 1
    assert rows[0]["location_id"] == new_id

    # 3. Verify All Cols & Get Baseline
    features = features_dict["locations"]
    all_rows = read.view_locations(1, connection, columns=features)
    returned_features = all_rows[0].keys()
    
    for feature in features:
        assert feature in returned_features
    assert len(features) == len(returned_features)

    # 4. Random Sampling
    max_rows = len(all_rows)
    if max_rows > 1:
        num_rows = random.randrange(1, max_rows)
    else:
        num_rows = 1

    num_rand_features = random.randrange(1, len(features))
    rand_features = random.sample(features, k=num_rand_features)
    
    rows = read.view_locations(1, connection, columns=rand_features, limit=num_rows)
    returned_features = rows[0].keys()
    
    for feature in rand_features:
        assert feature in returned_features
    assert len(rand_features) == len(returned_features)
    assert len(rows) == num_rows
    
    # 5. Delete Test
    delete.delete_location(1, new_id, conn=connection)
    connection.commit()
    
    rows_after = read.view_locations(1, connection)
    assert len(rows_after) == len(all_rows) - 1
    
    deleted_row = read.view_locations(1, connection, ids=new_id)
    assert len(deleted_row) == 0


def test_02_products_master(connection, features_dict, schema_types):
    cols = schema_types['products_master']
    
    # 1. Create
    new_id = create.add_product_master(
        tenant_id=1,
        product_code=generate_random_value(cols['product_code']),
        name=generate_random_value(cols['name']),
        storage_type=generate_random_value(cols['storage_type']),
        conn=connection
    )
    connection.commit()

    # 2. Verify Single Row
    rows = read.view_products_master(1, connection, ids=new_id)
    assert len(rows) == 1
    assert rows[0]["product_code"] == new_id

    # 3. Verify All Cols & Get Baseline
    features = features_dict["products_master"]
    all_rows = read.view_products_master(1, connection, columns=features)
    
    for feature in features:
        assert feature in all_rows[0].keys()
    assert len(features) == len(all_rows[0].keys())

    # 4. Random Sampling
    max_rows = len(all_rows)
    if max_rows > 1:
        num_rows = random.randrange(1, max_rows)
    else:
        num_rows = 1

    num_rand_features = random.randrange(1, len(features))
    rand_features = random.sample(features, k=num_rand_features)
    
    rows = read.view_products_master(1, connection, columns=rand_features, limit=num_rows)
    
    for feature in rand_features:
        assert feature in rows[0].keys()
    assert len(rand_features) == len(rows[0].keys()) # returned features are only requested ones
    assert len(rows) == num_rows

    # 5. Delete Test
    delete.delete_product_master(1, new_id, conn=connection)
    connection.commit()
    
    rows_after = read.view_products_master(1, connection)
    assert len(rows_after) == len(all_rows) - 1
    
    deleted_row = read.view_products_master(1, connection, ids=new_id)
    assert len(deleted_row) == 0


def test_03_drivers(connection, features_dict, schema_types):
    cols = schema_types['drivers']
    
    # 1. Create
    new_id = create.add_driver(
        tenant_id=1,
        name=generate_random_value(cols['name']),
        hourly_drive_wage=generate_random_value(cols['hourly_drive_wage']),
        hourly_load_wage=generate_random_value(cols['hourly_load_wage']),
        conn=connection
    )
    connection.commit()

    # 2. Verify Single Row
    rows = read.view_drivers(1, connection, ids=new_id)
    assert len(rows) == 1
    assert rows[0]["driver_id"] == new_id

    # 3. Verify All Cols & Get Baseline
    features = features_dict["drivers"]
    all_rows = read.view_drivers(1, connection, columns=features)
    
    for feature in features:
        assert feature in all_rows[0].keys()

    # 4. Random Sampling
    max_rows = len(all_rows)
    if max_rows > 1:
        num_rows = random.randrange(1, max_rows)
    else:
        num_rows = 1

    num_rand_features = random.randrange(1, len(features))
    rand_features = random.sample(features, k=num_rand_features)
    
    rows = read.view_drivers(1, connection, columns=rand_features, limit=num_rows)
    
    for feature in rand_features:
        assert feature in rows[0].keys()
    assert len(rows) == num_rows
    
    # 5. Delete Test
    delete.delete_driver(1, new_id, conn=connection)
    connection.commit()
    
    rows_after = read.view_drivers(1, connection)
    assert len(rows_after) == len(all_rows) - 1
    
    deleted_row = read.view_drivers(1, connection, ids=new_id)
    assert len(deleted_row) == 0


def test_04_vehicles(connection, features_dict, schema_types):
    cols = schema_types['vehicles']

    # 1. Create
    new_id = create.add_vehicle(
        tenant_id=1,
        name=generate_random_value(cols['name']),
        mpg=generate_random_value(cols['mpg']),
        depreciation_per_mile=generate_random_value(cols['depreciation_per_mile']),
        annual_insurance_cost=generate_random_value(cols['annual_insurance_cost']),
        annual_maintenance_cost=generate_random_value(cols['annual_maintenance_cost']),
        max_weight_lbs=generate_random_value(cols['max_weight_lbs']),
        max_volume_cubic_ft=generate_random_value(cols['max_volume_cubic_ft']),
            storage_type=generate_random_value(cols['storage_type']), 
        conn=connection
    )
    connection.commit()

    # 2. Verify Single Row
    rows = read.view_vehicles(1, connection, ids=new_id)
    assert len(rows) == 1
    assert rows[0]["vehicle_id"] == new_id

    # 3. Verify All Cols & Get Baseline
    features = features_dict["vehicles"]
    all_rows = read.view_vehicles(1, connection, columns=features)

    for feature in features:
        assert feature in all_rows[0].keys()

    # 4. Random Sampling
    max_rows = len(all_rows)
    if max_rows > 1:
        num_rows = random.randrange(1, max_rows)
    else:
        num_rows = 1

    num_rand_features = random.randrange(1, len(features))
    rand_features = random.sample(features, k=num_rand_features)
    
    rows = read.view_vehicles(1, connection, columns=rand_features, limit=num_rows)
    
    for feature in rand_features:
        assert feature in rows[0].keys()
    assert len(rows) == num_rows
    
    # 5. Delete Test
    delete.delete_vehicle(1, new_id, conn=connection)
    connection.commit()
    
    rows_after = read.view_vehicles(1, connection)
    assert len(rows_after) == len(all_rows) - 1
    
    deleted_row = read.view_vehicles(1, connection, ids=new_id)
    assert len(deleted_row) == 0


def test_05_entities(connection, features_dict, schema_types):
    cols = schema_types['entities']
    
    # 1. Create
    new_id = create.add_entity(
        tenant_id=1,
        name=generate_random_value(cols['name']),
        entity_min_profit=generate_random_value(cols['entity_min_profit']),
        conn=connection
    )
    connection.commit()

    # 2. Verify Single Row
    rows = read.view_entities(1, connection, ids=new_id)
    assert len(rows) == 1
    assert rows[0]["entity_id"] == new_id

    # 3. Verify All Cols & Get Baseline
    features = features_dict["entities"]
    all_rows = read.view_entities(1, connection, columns=features)
    
    for feature in features:
        assert feature in all_rows[0].keys()

    # 4. Random Sampling
    max_rows = len(all_rows)
    if max_rows > 1:
        num_rows = random.randrange(1, max_rows)
    else:
        num_rows = 1

    num_rand_features = random.randrange(1, len(features))
    rand_features = random.sample(features, k=num_rand_features)
    
    rows = read.view_entities(1, connection, columns=rand_features, limit=num_rows)
    
    for feature in rand_features:
        assert feature in rows[0].keys()
    assert len(rows) == num_rows
    
    # 5. Delete Test
    delete.delete_entity(1, new_id, conn=connection)
    connection.commit()
    
    rows_after = read.view_entities(1, connection)
    assert len(rows_after) == len(all_rows) - 1
    
    deleted_row = read.view_entities(1, connection, ids=new_id)
    assert len(deleted_row) == 0


def test_06_supply(connection, features_dict, schema_types):
    cols = schema_types['supply']
    
    # 1. Fetch Existing Dependencies (Assumes DB is populated)
    entities = read.view_entities(1, connection)
    ent_id = random.choice(entities)['entity_id']
    
    locations = read.view_locations(1, connection)
    loc_id = random.choice(locations)['location_id']
    
    products = read.view_products_master(1, connection)
    prod_id = random.choice(products)['product_code']

    # 2. Create Target
    new_id = create.add_supply(
        tenant_id=1,
        entity_id=ent_id,
        location_id=loc_id,
        product_code=prod_id,
        quantity_available=generate_random_value(cols['quantity_available']),
        unit_weight_lbs=generate_random_value(cols['unit_weight_lbs']),
        unit_volume_cu_ft=generate_random_value(cols['unit_volume_cu_ft']),
        items_per_handling_unit=generate_random_value(cols['items_per_handling_unit']),
        cost_per_item=generate_random_value(cols['cost_per_item']),
        conn=connection
    )
    connection.commit()

    # 3. Verify Single Row
    rows = read.view_supply(1, connection, ids=new_id)
    assert len(rows) == 1
    assert rows[0]["supply_id"] == new_id

    # 4. Verify All Cols & Get Baseline
    features = features_dict["supply"]
    all_rows = read.view_supply(1, connection, columns=features)
    
    for feature in features:
        assert feature in all_rows[0].keys()

    # 5. Random Sampling
    max_rows = len(all_rows)
    if max_rows > 1:
        num_rows = random.randrange(1, max_rows)
    else:
        num_rows = 1

    num_rand_features = random.randrange(1, len(features))
    rand_features = random.sample(features, k=num_rand_features)
    
    rows = read.view_supply(1, connection, columns=rand_features, limit=num_rows)
    
    for feature in rand_features:
        assert feature in rows[0].keys()
    assert len(rows) == num_rows
    
    # 6. Delete Test
    delete.delete_supply(1, new_id, conn=connection)
    connection.commit()
    
    rows_after = read.view_supply(1, connection)
    assert len(rows_after) == len(all_rows) - 1
    
    deleted_row = read.view_supply(1, connection, ids=new_id)
    assert len(deleted_row) == 0


def test_07_demand(connection, features_dict, schema_types):
    cols = schema_types['demand']
    
    # 1. Fetch Existing Dependencies
    locations = read.view_locations(1, connection)
    loc_id = random.choice(locations)['location_id']

    products = read.view_products_master(1, connection)
    prod_id = random.choice(products)['product_code']

    # 2. Create Target
    new_id = create.add_demand(
        tenant_id=1,
        location_id=loc_id,
        product_code=prod_id,
        quantity_needed=generate_random_value(cols['quantity_needed']),
        max_price=generate_random_value(cols['max_price']),
        conn=connection
    )
    connection.commit()

    # 3. Verify Single Row
    rows = read.view_demand(1, connection, ids=new_id)
    assert len(rows) == 1
    assert rows[0]["demand_id"] == new_id

    # 4. Verify All Cols & Get Baseline
    features = features_dict["demand"]
    all_rows = read.view_demand(1, connection, columns=features)
    
    for feature in features:
        assert feature in all_rows[0].keys()

    # 5. Random Sampling
    max_rows = len(all_rows)
    if max_rows > 1:
        num_rows = random.randrange(1, max_rows)
    else:
        num_rows = 1

    num_rand_features = random.randrange(1, len(features))
    rand_features = random.sample(features, k=num_rand_features)
    
    rows = read.view_demand(1, connection, columns=rand_features, limit=num_rows)
    
    for feature in rand_features:
        assert feature in rows[0].keys()
    assert len(rows) == num_rows
    
    # 6. Delete Test
    delete.delete_demand(1, new_id, conn=connection)
    connection.commit()
    
    rows_after = read.view_demand(1, connection)
    assert len(rows_after) == len(all_rows) - 1
    
    deleted_row = read.view_demand(1, connection, ids=new_id)
    assert len(deleted_row) == 0


def test_08_routes(connection, features_dict, schema_types):
    cols = schema_types['routes']
    
    # 1. Fetch locations for FKs
    locations = read.view_locations(1, connection)
    locs = random.sample(locations, 2)
    loc_a = locs[0]['location_id']
    loc_b = locs[1]['location_id']

    # 2. Create Target
    new_id = create.add_route(
        tenant_id=1,
        name=generate_random_value(cols['name']),
        origin_location_id=loc_a,
        dest_location_id=loc_b,
        conn=connection
    )
    connection.commit()

    # 3. Verify Single Row
    rows = read.view_routes(1, connection, ids=new_id)
    assert len(rows) == 1
    assert rows[0]["route_id"] == new_id

    # 4. Verify All Cols & Get Baseline
    features = features_dict["routes"]
    all_rows = read.view_routes(1, connection, columns=features)
    
    for feature in features:
        assert feature in all_rows[0].keys()

    # 5. Random Sampling
    max_rows = len(all_rows)
    if max_rows > 1:
        num_rows = random.randrange(1, max_rows)
    else:
        num_rows = 1

    num_rand_features = random.randrange(1, len(features))
    rand_features = random.sample(features, k=num_rand_features)
    
    rows = read.view_routes(1, connection, columns=rand_features, limit=num_rows)
    
    for feature in rand_features:
        assert feature in rows[0].keys()
    assert len(rows) == num_rows
    
    # 6. Delete Test
    delete.delete_route(1, new_id, conn=connection)
    connection.commit()
    
    rows_after = read.view_routes(1, connection)
    assert len(rows_after) == len(all_rows) - 1
    
    deleted_row = read.view_routes(1, connection, ids=new_id)
    assert len(deleted_row) == 0