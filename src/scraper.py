# scraper.py
# flight_prices_trends

# module containing stuff pertaining
# to scraping the info from skyscanner. 

# NL, 16/12/23
# NL, 17/12/23 -- moving from skyscanner to kayak, working out
#                 base functionality, config, etc.

############
# IMPORTS 
############
from dotenv import load_dotenv
import os
import yaml
import logging

import datetime as dt 
import re

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

# from bs4 import BeautifulSoup

load_dotenv()

############
# PATHS & CONSTANTS 
############
CHROMEDRIVER = os.getenv('CHROMEDRIVER')
# URL = 'https://www.skyscanner.de/transport/fluge/fran/del/231229/240123/?adultsv2=1&cabinclass=economy&childrenv2=&inboundaltsenabled=false&outboundaltsenabled=false&preferdirects=false&ref=home&rtn=1'
URL = 'https://www.kayak.co.uk/flights/FRA-DEL/2023-12-29/2024-01-23'

CONFIG = yaml.load(open('config.yaml'), Loader=yaml.FullLoader)
COUNTRY = 'uk'

############
# INIT 
############
# selenium
options = Options()
# options.add_argument("--headless=new")
# options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537")
driver = webdriver.Chrome(service=Service(executable_path=CHROMEDRIVER), options=options)

############
# FUNCTIONS 
############
# helpers
def discard_before_time_substring(s: str) -> str:
    '''
    we know that the first relevant
    bit of info in a flight info string
    is the departure time, which is always
    a string like '20:30 - 10:05'.

    we discard every substring before this.
    '''
    pattern = r'\d{2}:\d{2} – \d{2}:\d{2}'

    # Find the first match in the string
    match = re.search(pattern, s)

    if match:
        # If a match is found, discard everything before it
        return s[match.start():]
    else:
        # If no match is found, return the original string
        return s
    

def journey_is_ad(journey: list) -> bool:
    '''
    we sometimes get journeys which 
    are promoted ads, and shouldn't
    bias our understanding of what the
    `best` journeys are for a given
    query. 
    hence, let's remove those options. 
    '''
    for elem in journey:
        if elem=='Ad':
            return True
    return False


def find_timing_chunks(journey: list) -> list:
    '''
    the timings of a journey are
    formatted as 'HH:MM – HH:MM',
    and they neatly segment our journey
    into separate elements. by identifying
    the chunks containing these strings, 
    we can separate our journey into legs
    and parse all data more easily.
    '''
    pattern = r'\d{2}:\d{2} – \d{2}:\d{2}'
    indexes = []
    # find the indexes in `journey`
    # where the pattern matches
    for i, elem in enumerate(journey):
        if re.search(pattern, elem):
            indexes.append(i)
    
    return indexes


def find_last_duration_chunk(journey: list) -> int:
    '''
    for the last leg of a journey,
    the duration_chunk, formatted as
    '14h 15m', bookends the last chunk,
    and is indicative of the 
    price/meta section.
    '''
    pattern = r'\d+h \d+m'
    indexes = []
    
    for i, elem in enumerate(journey):
        if re.search(pattern, elem):
            indexes.append(i)
    
    return indexes[-1]


def parse_duration(s: str) -> dt.timedelta:
    '''
    our duration objects are strings
    in the format '14h 15m'. we want
    to parse this into a timedelta object.
    '''
    # split the string
    hours, minutes = s.split('h')
    minutes = minutes[:-1]
    # convert to timedelta
    return dt.timedelta(hours=int(hours), minutes=int(minutes))


def is_airport_chunk(s: str) -> bool:
    '''
    tests whether a given substring
    represents an airport
    format: 'AAAAname of airport'
    '''
    pattern = r'[A-Z]{4}'
    match = re.search(pattern, s)
    if match:
        return True
    else:
        return False


def parse_timings(s: str, 
                  departure_date: str,
                  penalty: int | None) -> tuple[dt.datetime]:
    '''
    in our journey info strings, we have
    a departure time and an arrival time,
    both contained in a substring in the
    following format: 

    '10:45 – 04:50'

    by combining the departure date,
    with the parsed time strings, 
    plus, if required, a penalty 
    (for when a flight arrives on a 
    different date than it set off),
    we output two datetime objects.
    '''
    # split the string
    times = s.split(' – ')

    ts0 = departure_date + ' ' + times[0]
    if penalty:
        penalty = dt.timedelta(days=penalty)
        ts1 = dt.datetime.strptime(departure_date, '%Y-%m-%d') + penalty
        # back to string
        ts1 = ts1.strftime('%Y-%m-%d') + ' ' + times[1]
    else:
        ts1 = departure_date + ' ' + times[1]

    t0 = dt.datetime.strptime(ts0, '%Y-%m-%d %H:%M')
    t1 = dt.datetime.strptime(ts1, '%Y-%m-%d %H:%M')

    return t0, t1


def chunk_is_penalty(s: str) -> int | None:
    '''
    we call a chunk a penalty if it
    indicates that a flight arrives
    on a different day to when it
    set off. this is indicated by
    a '+' followed by an integer.
    '''
    pattern = r'\+\d+'
    match = re.search(pattern, s)
    if match:
        # extract the integer
        logging.debug(f'penalty chunk found: {s[match.start():match.end()]}')
        return int(s[match.start()+1:match.end()])
    else:
        logging.debug(f'no penalty chunk found')
        return None


def find_parse_stops(s: str) -> int:
    '''
    takes a string and returns the
    number of stops in the journey.
    '''
    pattern = r'(\d+ stop)|direct'
    
    match = re.search(pattern, s)
    if match:
        # extract the integer
        logging.debug(f'stops chunk found: {s[match.start():match.end()]}')
        stops = s[match.start():match.end()]
        if stops == 'direct':
            return 0
        else:
            return int(stops.split()[0])
    else:
        logging.debug(f'no stops chunk found')
        return None
    

def find_parse_stop_airports(leg: list[str]) -> list:
    '''
    takes a substring and returns the
    stop airports for a given leg
    of a journey.
    '''
    # find the stop chunks
    # we know that the airports
    # where we stop are always
    # after the chunk with number of
    # stops
    for i, chunk in enumerate(leg):
        stops = find_parse_stops(chunk)
        if stops is not None:
            index = i+1
            break
    
    return leg[index].split(', ')

# prices/meta helpers
def parse_prices_meta(raw_chunks: list[str],
                      currency_symbol: str,
                      created_at: dt.datetime) -> dict:
    '''
    takes a list of strings containing
    the price and meta info for a given
    journey, and returns a dict with
    the parsed info.
    '''
    # first, drop 'Select' and ensure 
    # we have a list of length 5
    chunks = [x for x in raw_chunks if x != 'Select']
    if len(chunks) != 5:
        raise ValueError(f'chunks is not length 5: {chunks}')
    
    # parse the price to int
    raw_price = chunks[3]
    raw_price.replace(currency_symbol, '')
    price = int(raw_price)
    
    return {
        'airline' : chunks[0],
        'cabin_baggage' : chunks[1],
        'checked_baggage' : chunks[2],
        'class' : chunks[4],
        'price' : price,
        'currency' : currency_symbol,
        'created_at' : created_at
    }


    
# the scraper class
class FlightsScaper:
    '''
    a class that contains and manages all relevant
    data and tasks pertaining to retrieving flight
    data from kayak. 
    '''
    def __init__(self, browser_driver: str, country: str):
        self.driver = webdriver.Chrome(service=Service(executable_path=browser_driver)) 
        if country in CONFIG['permitted_countries']:
            self.country = country
        else:
            raise ValueError(f'{country} not in list of permitted countries')

        self.base_url = CONFIG['country'][self.country]['base_url']
        logging.info(f'FlightsScraper initialised with country {self.country} base url {self.base_url}')
        

    def new_journey(self,
                    journey_type: str,
                    origin: str | list[str],
                    destination: str | list[str],
                    leave_date: str | list[str],
                    return_date: str | None,
                    flex: str | int | None):
        '''
        creates a new journey object 
        with a journey_type. journey_type
        can be the standard 3:
        
        - one-way
        - return
        - multi-city

        but also a version we call 'city_options',
        which allows the user to compare mutliple
        origins/destinations as one journey,
        e.g. 'BRU,AMS,CGN-DEL'.
        '''
        if journey_type not in CONFIG['permitted_journey_types']:
            raise ValueError(f'{journey_type} not a permitted journey type')
        
        # validate inputs
        for input in [origin, destination]:
            # max number of city options
            if len(input) > CONFIG['max_city_options']:
                raise ValueError(f'Number of {input} exceeds permitted maximum of {CONFIG["max_city_options"]}')
            
            # validate iata codes
            if isinstance(input, str):
                input = [input]
            for code in input:
                self._validate_iata_code(code)
            
        # validate dates
        if isinstance(leave_date, str):
            leave_date = [leave_date]
        for date in leave_date:
            self._validate_date(date)
            
        if return_date is not None:
            self._validate_date(return_date)
        
        # add this stuff to our class
        self.journey_type = journey_type
        self.origin = origin
        self.destination = destination
        self.leave_date = leave_date
        self.return_date = return_date
        self.flex = flex

        # build url
        urls = []
        if 'city_options' in journey_type:
            for input in [origin, destination]:
                if isinstance(input, str):
                    input = [input]
            for o in origin:
                for d in destination:
                    logging.info(f'building url for {o}-{d}')
                    url = self._build_url(o, d, leave_date, return_date, flex, self.base_url)
                    logging.info(f'built url: {url}')
                    urls.append(url)

        else:
            url = self._build_url(
                origin, 
                destination, 
                leave_date, 
                return_date, 
                flex, 
                self.base_url)
            logging.info(f'built url: {url}')
            urls.append(url)
            
        self.urls = urls


    def get_flight_options(self,
                           url: str) -> list:
        '''
        loads the url, scrapes the options,
        returns a list of dict with prices.
        '''
        # load url
        self.driver.get(url)

        # click the cookie decline button,
        # if it exists
        try:
            button = driver.find_element(
                By.XPATH, 
                CONFIG['country'][self.country]['cookie_decline_button'])
            button.click()
        except NoSuchElementException:
            # no button - no problem
            pass
        
        # get results
        results = self.driver.find_elements(
            By.XPATH,
            CONFIG['country'][self.country]['result_blocks'])
        


    def write_data():
        pass
    

    @staticmethod
    def _build_url(origin: str | list[str],
                   destination: str | list[str], 
                   leave_date: str | list[str],
                   return_date: str | None,
                   flex: str | int | None,
                   base_url: str) -> str:
        '''
        builds a url for a given journey. 
        if 'origin' or 'destination' are lists,
        then the function will build a url for
        a multi-city itinerary, in which case the
        'return_date' arguments is ignored, and 
        all origin, destination and leave_date
        arguments must be lists of equal length.
        '''
        # check inputs go with our journey type,
        # define journey type
        if (isinstance(origin, list) and
            isinstance(destination, list) and
            isinstance(leave_date, list) and
            len(origin) == len(destination) == len(leave_date) and
            return_date is None and
            flex is None):
            journey_type = 'multi-city'
        elif (isinstance(origin, str) and isinstance(destination, str) and isinstance(leave_date, str)):
            if return_date is None:
                journey_type = 'one-way'
            elif isinstance(return_date, str):
                journey_type = 'return' 
        else:
            raise ValueError('Invalid combination of input parameters.')   
        logging.info(f'journey type: {journey_type}')

        # check flex_type is valid
        flex_add=''
        if flex is not None:
            if isinstance(flex, int) and (flex==-1 or (flex>=1 and flex<=3)):
                flex = str(flex)
            logging.info(f'flex: {flex}')
            flex_add = '-'+CONFIG['permitted_flex'][flex]
        
        # build url
        if journey_type == 'one-way':
            url = base_url + origin + '-' + destination + '/' + leave_date + flex_add
        elif journey_type == 'return':
            url = base_url + origin + '-' + destination + '/' + leave_date + flex_add + '/' + return_date + flex_add
        elif journey_type == 'multi-city':
            url = base_url 
            for i in range(len(origin)):
                url += origin[i] + '-' + destination[i] + '/' + leave_date[i] + '/'
        else:
            raise ValueError('Invalid combination of input parameters.')    
        
        logging.info(f'built url: {url}')
        return url
    

    @staticmethod
    def _validate_date(date: str) -> str:
        '''
        we need date strings to be
        in the format YYYY-MM-DD.
        this function takes a date string
        and checks it's valid, and if so
        returns it as is, otherwise raises
        a ValueError.
        '''
        try:
            dt.datetime.strptime(date, '%Y-%m-%d')
            return date
        except ValueError:
            raise ValueError("Incorrect data format, should be YYYY-MM-DD")     


    @staticmethod
    def _validate_iata_code(code: str) -> str:
        '''
        takes a string and checks it satisfies
        the iata code format, i.e. 3 letters,
        not other characters.
        '''
        if len(code) == 3 and code.isalpha():
            return code
        else:
            raise ValueError(f'{code} needs to be len==3, only letters.')
        
    
    @staticmethod
    def _parse_journey_info(scraped_journey: str,
                            dates: list[str],
                            journey_type: str) -> dict:
        '''
        takes a scraped string containing flight 
        info for one flight and parses it into a 
        dict.

        this stuff is all a bit in flux, and 
        we have to ascertain whether a given chunk
        is what we think it is as a function of
        a) where it is in the sequence of chunks, and
        b) its contents.
        '''
        # remove random ad stuff before flight info
        scraped_journey = discard_before_time_substring(scraped_journey)

        # split
        raw_chunks = scraped_journey.split('\n')

        # drop if ad
        if journey_is_ad(raw_chunks):
            return None
        
        # identify number of legs by
        # finding chunks with timings.
        indexes = find_timing_chunks(raw_chunks)
        legs = []
        for i, index in enumerate(indexes):
            if i+1 < len(indexes):
                legs.append(raw_chunks[index:indexes[i+1]])
            else:
                # last leg - find the duration chunk
                duration_index = find_last_duration_chunk(raw_chunks)
                legs.append(raw_chunks[index:duration_index+1])

                # now, append the price/meta chunk
                prices_meta = raw_chunks[duration_index+1:]

        # ensure that we have the same number of
        # dates as legs
        if len(dates) != len(legs):
            raise ValueError(
                f'Number of dates ({len(dates)}) does not match number of legs ({len(legs)})')

        # iterate over legs, compiling our out dict
        legs_out = []

        for i, leg in enumerate(legs):
            # check if we have a penalty
            for chunk in leg:
                penalty = chunk_is_penalty(chunk)
                if penalty:
                    break
        
            # we know that index 0 is the timings
            dep, arr = parse_timings(leg[0], dates[i], penalty)

            # find the airport chunks
            airports = []
            for chunk in leg:
                if is_airport_chunk(chunk):
                    airports.append(chunk[:3])

            # find number of stops
            for chunk in leg:
                stops = find_parse_stops(chunk)
                if stops is not None:
                    break

            # find stop airports, if any
            stopovers = find_parse_stop_airports(leg)

            # find & parse duration
            duration = leg[find_last_duration_chunk(leg)]
            duration = parse_duration(duration)

            # append to legs_out
            legs_out.append({
                'departure_timestamp': dep,
                'arrival_timestamp': arr,
                'departure_airport': airports[0],
                'arrival_airport': airports[1],
                'duration': duration,
                'n_stops': stops,
                'stopover_airports': stopovers
            })
            
        # parse price/meta chunk
        meta_out = parse_prices_meta(prices_meta)
        out = {'legs': legs_out, 'meta': meta_out}
        
        return out


'''
TO DO:
- finish off the flight info parsing function, 
  we need to have this be very robust to all 
  the intricacies and differences of how the
  info is presented on the page.
- see what's up with the different xpath/
  country combinations. do they change randomly?
- write the function for writing the data to
  file or db. 
- test all this stuff, and see whether we can get it
  to work on the server.

'''



############
# THE THING! 
############
driver.get(URL)

# click the cookie decline button
div = driver.find_element(By.CLASS_NAME, 'P4zO-submit-buttons')
button = div.find_element(By.TAG_NAME, 'button')
button.click()

# results_page = BeautifulSoup(driver.page_source, 'html.parser')

all_results = driver.find_elements(By.XPATH, PATHS['result_blocks'])

for result in all_results:
    print(result.text)
    print('---')

