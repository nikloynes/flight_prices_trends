# db_utils.py
# flight_prices_trends

# module for interfacing with
# the sqlite3 database, 
# primarily data IO

# NOTE: to init a new db, run
# sqlite3 <db_name>.db < schema.sql
# this will overwrite any existing 
# data if your db already exists.

# NL, 19/12/23

############
# IMPORTS 
############
import os
from dotenv import load_dotenv
import yaml
import logging

import sqlite3
from src.id_factory import Journey, FlightSearch

############
# INIT
############
logging.getLogger('db_utils')

load_dotenv()

############
# PATHS & CONSTANTS 
############
DB_PATH = os.getenv('DB_PATH')

INSERT_MAP = yaml.load(open('config.yaml'), Loader=yaml.FullLoader)['insert_map']

############
# FUNCTIONS 
############
# helpers
def flatten_list(l: list) -> str:
    '''
    flattens a list of strings
    into a single string, separated
    by commas.
    '''
    return ', '.join(l)


# def prices_drop_duplicates(data: list[tuple]) -> list[tuple]:
#     '''
#     sometimes, for prices,
#     we get verbatim duplicates. 
#     for journeys and legs this doesn't
#     matter, as the primary key is
#     generated from the data itself and
#     thus we won't be left with dupes in
#     the db. for prices, however, it helps
#     to drop these dupes.

#     NOTE: run this after extracting the
#     prices from journey_options.
#     '''


# extracting data
# for sql tables
def extract_journeys(data: list[dict],
                     search_id: str) -> list[tuple]:
    '''
    extracts the base journey 
    object from journey_options
    data. returns a list of tuples
    which can be inserted into the
    db.
    '''
    journeys = []

    for record in data:
        journey_id = Journey(**record).create_id()
        n_legs = len(record['legs'])
        cabin_baggage = record['meta']['cabin_baggage']
        checked_baggage = record['meta']['checked_baggage']
        class_ = record['meta']['class'][0]

        journeys.append(
            (journey_id, 
             search_id, 
             n_legs, 
             cabin_baggage, 
             checked_baggage, 
             class_))
    
    return journeys


def extract_legs(data: list[dict]) -> list[tuple]:
    '''
    extracts the individual legs 
    from journey_options data.
    '''
    legs = []

    for record in data:
        journey_id = Journey(**record).create_id()

        for i, leg in enumerate(record['legs']):
            leg_id = journey_id + f'_{i+1}'
            leg_number = i+1

            departure_time = leg['departure_timestamp'].isoformat()
            arrival_time = leg['arrival_timestamp'].isoformat()
            departure_airport = leg['departure_airport']
            arrival_airport = leg['arrival_airport']
            duration = leg['duration'].total_seconds()
            n_stops = leg['n_stops']
            if 'stopover_airports' not in leg.keys():
                stopover_airports = None
            if isinstance(leg['stopover_airports'], list):
                stopover_airports = flatten_list(leg['stopover_airports'])
            else:
                stopover_airports = leg['stopover_airports']

            legs.append((
                leg_id, 
                journey_id, 
                leg_number, 
                departure_time, 
                arrival_time, 
                departure_airport, 
                arrival_airport, 
                duration,
                n_stops,
                stopover_airports))
    
    return legs


def extract_prices(data: list[dict]) -> list[tuple]:
    '''
    extract the prices 
    and related data from 
    journey_options data.

    this is a bit different
    from the other things
    we're extacting, as here
    we kind of need to make sure
    we're not inserting duplicates.
    so, before we add to the list,
    we check if the combo of journey_id,
    price and currency already exists 
    IN OUR LIST, not the db.
    '''
    prices = []

    for record in data:
        journey_id = Journey(**record).create_id()

        price = record['meta']['price']
        currency = record['meta']['currency']
        created_at = record['meta']['created_at'].isoformat()

        dupe = False
        for p in prices:
            if journey_id == p[0] and price == p[1] and currency == p[2]:
                logging.info(f'found duplicate price: {p}')
                dupe = True
                break
        
        if dupe:
            continue

        prices.append((journey_id, price, currency, created_at))
    
    return prices


def parse_flight_search(data: dict) -> tuple:
    '''
    parse a flight search,
    and create the search_id
    for it. returns a tuple
    ready for insertion into
    the db.
    '''
    search_id = FlightSearch(**data).create_id()

    journey_type = data['journey_type']
    
    if isinstance(data['origin'], list): 
        origin = flatten_list(data['origin'])
    else:
        origin = data['origin']

    if isinstance(data['destination'], list):
        destination = flatten_list(data['destination'])
    else:
        destination = data['destination']

    if isinstance(data['leave_date'], list):
        leave_date = flatten_list([x.isoformat() for x in data['leave_date']])
    else:
        leave_date = data['leave_date'].isoformat()
    
    if 'return_date' in data.keys():
        return_date = data['return_date'].isoformat()
    else:
        return_date = None
    
    if 'flex' in data.keys():
        flex = data['flex']
    else:
        flex = None

    return (
        search_id, 
        journey_type, 
        origin, 
        destination, 
        leave_date, 
        return_date, 
        flex
        )


# inserting data
def execute_insert_query(table: str, 
                         columns: list[str],
                         data: list[tuple] | tuple):
    '''
    using our INSERT_MAP dict, 
    we can dynamically create
    our queries for inserting 
    data into the db.

    the data generated from 
    the functions in this module
    should match the order of
    the columns in the INSERT_MAP.
    '''
    if table not in INSERT_MAP.keys():
        raise ValueError(f'table {table} not in INSERT_MAP')
    if columns != INSERT_MAP[table]:
        raise ValueError(f'columns {columns} do not match INSERT_MAP for table {table}')
    
    columns_fmtd = f'({", ".join(columns)})'
    values_fmtd = f'({", ".join(["?" for _ in columns])})'

    q = f'''
        INSERT OR IGNORE INTO {table} {columns_fmtd}
        VALUES {values_fmtd}
        '''
    
    logging.info(f'built query: {q}')

    if isinstance(data, tuple):
        data = [data]

    with sqlite3.connect(DB_PATH) as conn:
        logging.debug(f'connected to db at {DB_PATH}')
        
        cursor = conn.cursor()
        logging.debug(f'created cursor')

        cursor.executemany(q, data)
        logging.debug(f'executed query')
        
        conn.commit()
        logging.debug(f'committed changes')
        
        # conn.close()
        # logging.debug(f'closed connection')

    return True
