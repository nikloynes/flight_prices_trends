# id_factory.py
# flight_prices_trends

# module for creating/retrieving 
# custom id strings for flight-
# related stuff, i.e.

# journeys,
# flight-searches

# and also to validate the data before
# ids are generated (and stored)

# NL, 19/12/23

############
# IMPORTS 
############
import logging

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, timedelta

import hashlib

############
# INIT
############
logging.getLogger('id_factory')

############
# PATHS & CONSTANTS 
############
JOURNEY_ID = {
    'legs' : [
        'departure_timestamp',
        'arrival_timestamp',
        'departure_airport',
        'arrival_airport',
        'n_stops',
        'stopover_airports'
    ],
    'meta' : ['airline']
}

############
# DATA MODELS
############
# journey
class Leg(BaseModel):
    departure_timestamp: datetime
    arrival_timestamp: datetime
    departure_airport: str
    arrival_airport: str
    duration: timedelta
    n_stops: int
    stopover_airports: Optional[List[str]]


class Meta(BaseModel):
    airline: List[str]
    cabin_baggage: int
    checked_baggage: int
    class_: List[str] = Field(alias='class')
    price: int
    currency: str
    created_at: datetime


class Journey(BaseModel):
    legs: List[Leg]
    meta: Meta

    def create_id(self):
        '''
        creates a unique journey_id which 
        should encompass only the components 
        of the journey not subject to change
        '''
        journey_dict = self.model_dump()

        journey_string = ''
        for leg in journey_dict['legs']:
            journey_string += '-'.join([str(leg[x]) for x in JOURNEY_ID['legs']])
        journey_string += '-'.join([str(journey_dict['meta'][x]) for x in JOURNEY_ID['meta']])
        logging.info(f'compiled unique journey string: {journey_string}')

        journey_id = hashlib.sha256(journey_string.encode()).hexdigest()
        logging.info(f'created journey_id: {journey_id}')

        return journey_id


# flight search
class FlightSearch(BaseModel):
    journey_type: str
    origin: str
    destination: str
    leave_date: datetime | List[datetime]
    return_date: Optional[datetime] = None
    flex: Optional[int] = None

    def create_id(self):
        '''
        creates a hashed
        flight_search id
        '''
        flight_search_dict = self.model_dump()

        flight_search_string = '-'.join([str(flight_search_dict[x]) for x in flight_search_dict])
        logging.info(f'compiled unique flight_search string: {flight_search_string}')

        flight_search_id = hashlib.sha256(flight_search_string.encode()).hexdigest()
        logging.info(f'created flight_search_id: {flight_search_id}')

        return flight_search_id 