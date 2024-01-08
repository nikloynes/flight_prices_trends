# flight_prices_trends
flight prices change, sometimes unpredictably. this software lets you track the price and availability of very flexibly defined routes over time. this benefits both smart flight purchasing, and broader research on the dynamics of the flights market. 

Last updated: NL, 08/01/24

### tl, dr
`flight_prices_trends` is software that helps illuminate the mystery of flight prices, allowing you to track trends over a long period of time without having to visit sites and search for flights.  

at its core, the software incorporates a scraper for the ~~skyscanner~~ **k a y a k** flight price comparison website and a lean SQLite database to store the data. in the future, I aim to add an analytics suite to illuminate some of the dynamics of price changes, as well as a dashboard for visualising them. this software is a side project, and indeed an ongoing project. it is supplied without warranty of any kind. feel free to use, enjoy and contribute if you wish. 

### getting started
- make sure you have a `chromedriver` compatible with the version of chrome installed on your system. you will need to add the full path to it as `CHROMEDRIVER` in your `.env` file. 
- make sure you have `sqlite3` installed for your system. create a new instance of the database by running `sqlite3 your_db_name.sqlite < schema.sql`, and adding its full path as `DB_PATH` to `.env`.
- recommended: set up a `virtualenv`
- install all python dependencies: `pip install -r requirements.txt` 

### how to use
- the easiest way of using this software is to use the `get_flights.py` script. you can specify the parameters of your search as arguments to the script: 

```
usage: get_flights.py [-h] -j {one_way,round_trip,multi_city,city_options-one_way,city_options-round_trip} -d DEPARTURE_AIRPORT [DEPARTURE_AIRPORT ...] -a ARRIVAL_AIRPORT
                    [ARRIVAL_AIRPORT ...] -f FROM_DATE [FROM_DATE ...] [-t [TO_DATE]] [-fl [{-1,+1,1,2,3}]] [-c {de,us,uk}] [-l]

args for getting flights

options:
-h, --help            show this help message and exit
-j {one_way,round_trip,multi_city,city_options-one_way,city_options-round_trip}, --journey_type {one_way,round_trip,multi_city,city_options-one_way,city_options-round_trip}
                        journey type of search
-d DEPARTURE_AIRPORT [DEPARTURE_AIRPORT ...], --departure_airport DEPARTURE_AIRPORT [DEPARTURE_AIRPORT ...]
                        departure airport code
-a ARRIVAL_AIRPORT [ARRIVAL_AIRPORT ...], --arrival_airport ARRIVAL_AIRPORT [ARRIVAL_AIRPORT ...]
                        arrival airport code
-f FROM_DATE [FROM_DATE ...], --from_date FROM_DATE [FROM_DATE ...]
                        from; leave date for the journey. format: YYYY-MM-DD
-t [TO_DATE], --to_date [TO_DATE]
                        to; return date for the journey. format: YYYY-MM-DD
-fl [{-1,+1,1,2,3}], --flex [{-1,+1,1,2,3}]
                        flexibility of dates
-c {de,us,uk}, --country {de,us,uk}
                        country/domain ending of flights site
-l, --log_to_stdout   print logging msgs to stdout
```
- running `get_flights.py` will perform your search and write the options to your sqlite database. 
- in order to get journey options for the same flight_search regularly, add `get_flights.py` along with the desired arguments to your crontab. 

- you can also use all the functionality of the scraper interactively: 
    - run `from src.scraper import FlightScraper` 
    - init your class: `my_flight = FlightScraper(country='uk')`
    - then add a new journey_search:
    ```python
    my_flight.new_journey_search(
    journey_type='round_trip', 
    origin='LHR', 
    destination='LAX', 
    leave_date='2024-02-08',
    return_date='2024-02-25')
    ```
    - then, get your options: `my_flight.get_all_flight_options()`
    - and then, you could add all the collected flight options to your db like so:
    
    ```python
    flight_search = db.parse_flight_search(my_flight.get_journey_search())
    search_id = flight_search[0]
    journeys = db.extract_journeys(data=my_flight.journey_options, search_id=search_id)
    legs = db.extract_legs(data=my_flight.journey_options)
    prices = db.extract_prices(my_flight.journey_options)

    db.execute_insert_query(table='flight_searches', columns=db.INSERT_MAP['flight_searches'], data=flight_search)
    db.execute_insert_query(table='journeys', columns=db.INSERT_MAP['journeys'], data=journeys)
    db.execute_insert_query(table='legs', columns=db.INSERT_MAP['legs'], data=legs)
    db.execute_insert_query(table='prices', columns=db.INSERT_MAP['prices'], data=prices)
    ```
- the database is structure into 3 core tables, in (almost) ascending order of specificity:
    - `flight_searches`
    - `journeys`
    - `legs`
    - `prices`
- the tables link to each other to avoid duplication. 
    - a **flight_seach** is defined as a search for a journey (one-way, round-trip, multi-city, and 'city-options') between n airports at t dates. 
    - a **journey** is an option for an actual itinerary listed on the site which matches your flight_search
    - a **leg** is one part of a journey - which can be composed of n legs. a leg can contain stopovers, but separate stopovers do not themselves constitute legs, unless they are explicitly defined in a flight_search
    - a **price** is the recorded price (and currency) for a given journey when observed at a given time when the code was run. 
- additionally, there is a table called `compound_airport_codes`, which circumvents an issue whereby the `airportsdata` library is not aware of catch-all IATA airport codes, such as `LON` or `NYC` (stand-ins for all airports in the london or new york areas, respectively). users can add to this table if they encounter an unrecognised IATA code. 

### roadmap
- implement geckodriver (firefox) functionality - especially useful for linux systems
- look into socks5 proxies, implement into scraper (to avoid possible banning)
- look at what happens if we run headless
- try working out a way to run headless with x11 server (if true headless not possible, which is the assumption)
- write some tests!
- analytics suite:
    - stuff for everything that's in DB
        - distance
        - airline
    - stuff based on a given flight search
    - stuff based on regions / similar routes
        - simple descriptive stats
        - regression models
- basic dashboard (mainly for dynamic viz)

### notes:
- website owners like to change the xpaths and css_selectors on their sites, in order to prevent scraping. so, you may have to re-locate the relevant elements and update them in `config.yaml` if something isn't working; especially if you're getting errors from `selenium` 
- on MacOS, your chromedriver executable may be 'quarantined' by the OS. you can un-quarantine it (at your own risk -- make sure to download the driver from the official source only) by running  `xattr -d com.apple.quarantine path/to/chromedriver`

### comparisons & acknowledgments
there are a bunch of existing projects hosted on github which aimed to solve a similar problem. i used some of them to get inspiration and a better understanding of how to approach this particular problem, and would like to thank the authors for sharing their code. specifically, these are:

- `https://github.com/fnneves/flight_scraper` 
- `https://github.com/amal-hasni/kayak_scraper` 
- `https://github.com/MeshalAlamr/flight-price-prediction`  