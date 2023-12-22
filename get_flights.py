# get_flights.py
# flight_prices_trends

# a script we can use to 
# retrieve relevant flight data
# using our scraper, format/validate it
# and then store it in our database.

# NL, 22/12/23

############
# IMPORTS 
############
import os
from dotenv import load_dotenv
import sys
import logging
import argparse
from datetime import datetime

from src.scraper import FlightsScaper, CONFIG
import src.db_utils as db 

load_dotenv()

############
# CLI
############
# helper to auto-convert a single list arg
# to str rather than returning a list
class SingleOrListAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        if len(values) == 1:
            setattr(namespace, self.dest, values[0])
        else:
            setattr(namespace, self.dest, values)

parser = argparse.ArgumentParser(
    description='args for getting flights')

# -a ACTION_TYPE
parser.add_argument(
    '-j', 
    '--journey_type',
    choices=CONFIG['permitted_journey_types'],
    required=True,
    help='journey type of search')

parser.add_argument(
    '-d', 
    '--departure_airport',
    nargs='+',
    required=True,
    help='departure airport code',
    action=SingleOrListAction)

parser.add_argument(
    '-a', 
    '--arrival_airport',
    nargs='+',
    required=True,
    help='arrival airport code',
    action=SingleOrListAction)

parser.add_argument(
    '-f', 
    '--from_date',
    nargs='+',
    required=True,
    help='from; leave date for the journey. format: YYYY-MM-DD')

parser.add_argument(
    '-t', 
    '--to_date',
    nargs='?',
    required=False,
    default=None,
    help='to; return date for the journey. format: YYYY-MM-DD')

parser.add_argument(
    '-fl',
    '--flex',
    nargs='?',
    choices=CONFIG['permitted_flex'].keys(),
    required=False,
    default=None,
    help='flexibility of dates')

parser.add_argument(
    '-c',
    '--country',
    choices=CONFIG['permitted_countries'],
    default='uk',
    help='country/domain ending of flights site')

parser.add_argument(
    '-l', 
    '--log_to_stdout', 
    action='store_true',
    help= 'print logging msgs to stdout')    

args = parser.parse_args()

############
# INIT
############
todays_logfile = f'{datetime.now().strftime("%Y-%m-%d")}.log'
file_handler = logging.FileHandler(filename=os.getenv('LOG_FILE_PATH')+todays_logfile)
stdout_handler = logging.StreamHandler(sys.stdout)

if args.log_to_stdout:
    handlers = [file_handler, stdout_handler]
else: 
    handlers = [file_handler]

logging.basicConfig(
    level=logging.INFO, # change to DEBUG for messages from all the dependencies 
    format=os.getenv('LOG_FORMAT'),
    handlers=handlers)

############
# THE THING!
############
logging.info('flights scraper init')
my_flight = FlightsScaper(country=args.country)

logging.info('adding new flight search to my_flight')
my_flight.new_journey_search(
    journey_type=args.journey_type,
    origin=args.departure_airport,
    destination=args.arrival_airport,
    leave_date=args.from_date,
    return_date=args.to_date,
    flex=args.flex)

logging.info('getting flight options')
my_flight.get_all_flight_options()

logging.info('shutting down browser driver')
my_flight.driver.quit()

logging.info('parsing & validating data for insert into db')
flight_search = db.parse_flight_search(my_flight.get_journey_search())
search_id = flight_search[0]
journeys = db.extract_journeys(data=my_flight.journey_options, search_id=search_id)
legs = db.extract_legs(data=my_flight.journey_options)
prices = db.extract_prices(my_flight.journey_options)

logging.info('inserting data into db')
db.execute_insert_query(table='flight_searches', columns=db.INSERT_MAP['flight_searches'], data=flight_search)
db.execute_insert_query(table='journeys', columns=db.INSERT_MAP['journeys'], data=journeys)
db.execute_insert_query(table='legs', columns=db.INSERT_MAP['legs'], data=legs)
db.execute_insert_query(table='prices', columns=db.INSERT_MAP['prices'], data=prices)