# airport_utils.py
# flight_prices_trends

# contains functions related to
# airports - validating airport codes,
# extracting airport metadata,
# calculating distances 

# NL, 21/12/23

############
# IMPORTS 
############
import logging

import airportsdata
from typing import Literal
from math import radians, cos, sin, asin, sqrt

from src.db_utils import (
    match_compound_airport, 
    get_flight_component_by_id)

############
# INIT 
############
logging.getLogger('airport_utils')

airports = airportsdata.load('IATA') 

############
# FUNCTIONS 
############
def validate_airport_code(code: str,
                          ignore_case: bool = False) -> bool:
    '''
    validates an airport code
    using the airportsdata package
    '''
    if ignore_case:
        code = code.upper()

    if code not in airports:
        logging.info('checking compound codes in db')
        code = match_compound_airport(code)

    return code in airports


def get_airport_metadata(code: str,
                         ignore_case: bool = False,
                         return_type: Literal['dict', 'tuple'] = 'tuple',
                         fields: list = ['lat', 'lon']) -> dict | tuple:
    '''
    returns the metadata for a given
    airport code. can specify which 
    metadata is required, and which 
    type it gets returned as. 
    by default, it's a tuple of lat 
    and lon.
    '''
    if ignore_case:
        code = code.upper()

    if code not in airports:
        logging.info('checking compound codes in db')
        code = match_compound_airport(code)

    if return_type == 'dict':
        # select the fields we want
        return {field : airports[code][field] for field in fields}
    elif return_type == 'tuple':
        return tuple([airports[code][field] for field in fields])
    

def haversine(lon1: float, 
              lat1: float, 
              lon2: float, 
              lat2: float) -> float:
    '''
    NOTE: this function was adapted
    from a smart poster at 

    `https://stackoverflow.com/questions/
    4913349/haversine-formula-in-python-
    bearing-and-distance-between-two-gps-points`

    retrieved 21/12/23. 
    
    original docstring:

    Calculate the great circle distanc
    e in kilometers between two points 
    on the earth (specified in decimal degrees)
    '''
    # convert decimal degrees to radians 
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

    # haversine formula 
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 

    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a)) 
    r = 6371 # Radius of earth in kilometers. Use 3956 for miles. Determines return value units.
    
    return c * r


def calculate_distance(origin: str, 
                       destination: str) -> float:
    '''
    calculates the distance between
    two airports, given their codes.
    '''
    lat1, lon1 = get_airport_metadata(origin)
    lat2, lon2 = get_airport_metadata(destination)

    return haversine(lon1, lat1, lon2, lat2)


def calculate_absolute_leg_distance(leg: dict,
                                    leg_id: str | None) -> float:
    '''
    calculates the effective leg
    distance - that is the ground 
    covered, including stopovers of
    a given leg, as recorded in the
    db.
    '''
    if not leg and leg_id:
        logging.info(f'no leg supplied, trying to retrieve via leg-id')
        leg = get_flight_component_by_id('leg', leg_id)

    if leg['n_stops']==0:
        logging.info(f'no stopovers, returning direct distance')
        return calculate_distance(
            leg['departure_airport'], 
            leg['arrival_airport'])
    
    logging.info(f'calculating distance with stopovers')
    # split the string
    stopovers = leg['stopover_airports'].split(', ')

    total_distance = 0
    from_idx = 0
    to_idx = 1

    all_airports = [leg['departure_airport']] + stopovers + [leg['arrival_airport']]
    
    used_all_airports = False
    
    while not used_all_airports:
        if len(all_airports[to_idx].split('-'))>1:
            logging.info(f'{all_airports[to_idx]} is a self-transfer')  

    pass

'''
would be nice to finish off this function.
'''