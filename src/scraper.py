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

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By

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
# base stuff
class FlightsScaper:
    '''
    a class that contains and manages all relevant
    data and tasks pertaining to retrieving flight
    data from kayak. 
    '''
    def __init__(self, browser_driver: str, country: str):
        self.driver = webdriver.Chrome(service=Service(executable_path=browser_driver)) 
        if country in CONFIG['countries']:
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
        if 'city_options' in journey_type:
            for input in [origin, destination]:
                if isinstance(input, str):
                    input = [input]

        url = []
        if journey_type=='city_options-one_way':
            for o in origin:
                for d in destination:
                    url.append(self._build_url(o, d, leave_date, return_date, flex, self.base_url))


        self.url = self._build_url(origin, destination, leave_date, return_date, flex, self.base_url)


        pass

    def get_prices():
        pass

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

