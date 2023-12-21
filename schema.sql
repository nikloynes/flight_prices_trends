CREATE TABLE journeys (
    journey_id TEXT PRIMARY KEY,
    search_id TEXT,
    n_legs INTEGER,
    cabin_baggage INTEGER,
    checked_baggage INTEGER,
    class TEXT,
    FOREIGN KEY(search_id) REFERENCES flight_searches(search_id)
);

CREATE TABLE legs (
    leg_id TEXT PRIMARY KEY,
    journey_id INTEGER,
    leg_number INTEGER,
    departure_time TEXT,
    arrival_time TEXT,
    departure_airport TEXT,
    arrival_airport TEXT,
    duration INTEGER,
    n_stops INTEGER,
    stopover_airports TEXT,
    FOREIGN KEY(journey_id) REFERENCES journeys(journey_id)
);

CREATE TABLE prices (
    price_id INTEGER PRIMARY KEY AUTOINCREMENT,
    journey_id TEXT,
    price REAL,
    currency TEXT,
    created_at TIMESTAMP,
    FOREIGN KEY(journey_id) REFERENCES journeys(journey_id)
);

CREATE TABLE flight_searches (
    search_id TEXT PRIMARY KEY,
    journey_type TEXT,
    origin TEXT,
    destination TEXT,
    leave_date TEXT,
    return_date TEXT,
    flex INTEGER
);

CREATE TABLE searches_journeys_prices (
    search_id INTEGER,
    journey_id INTEGER,
    price_id INTEGER,
    PRIMARY KEY(search_id, journey_id, price_id),
    FOREIGN KEY(search_id) REFERENCES flight_searches(search_id),
    FOREIGN KEY(journey_id) REFERENCES journeys(journey_id),
    FOREIGN KEY(price_id) REFERENCES prices(price_id)
);

CREATE TABLE journeys_prices (
    journey_id INTEGER,
    price_id INTEGER,
    PRIMARY KEY(journey_id, price_id),
    FOREIGN KEY(journey_id) REFERENCES journeys(journey_id),
    FOREIGN KEY(price_id) REFERENCES prices(price_id)
);

CREATE TABLE compound_airport_codes (
    compound_code TEXT PRIMARY KEY,
    included_airport_code TEXT
);