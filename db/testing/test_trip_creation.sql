CALL generate_synthetic_data();

CALL get_planning_assets();

#create trip
CALL create_trip_header(
    1,          -- Route ID
    1,          -- Vehicle ID
    1,          -- Driver ID
    CURDATE(),  -- Run Date
    4.50,       -- Current Gas Price
    @my_trip_id -- RETURNS trip ID
);

#add 2 handling units of broccoli
CALL add_trip_item(
    @my_trip_id, -- trip ID
    1,           -- Supply ID 
    1,           -- Demand ID
    2.0          -- Quantity to Load
);
CALL add_trip_item(
    @my_trip_id, -- The Trip we just made
    2,           -- Supply ID 
    1,           -- Demand ID
    2.0          -- Quantity to Load
);

#get snapshot trip details 
CALL get_trip_details(@my_trip_id);

#check trigger that removes inventory
CALL get_planning_assets();

CALL delete_plan(@my_trip_id);

#check trigger that adds inventory back on delete
CALL get_planning_assets();