# flight_prices_trends
flight prices change, sometimes unpredictably. this software lets you track the price and availability of very flexibly defined routes over time. this benefits both smart flight purchasing, and broader research on the dynamics of the flights market. 

Last updated: NL, 21/12/23

### tl, dr
`flight_prices_trends` is software that helps illuminate the mystery of flight prices, allowing you to track trends over a long period of time without having to visit sites and search for flights.  

At its core, the software incorporates a scraper for the ~~skyscanner~~ **k a y a k** flight price comparison website, functionality for performing several, recurring scraper calls from different IP addresses via socks5 proxies (to avoid banning), a lean SQLite database to store the data, and some analytics to provide interpretation on what's going on with prices. 

### getting started
- make sure you have a `chromedriver` compatible with the version of chrome installed on your system. you will need to add the full path to it as `CHROMEDRIVER` in your `.env` file. 
- make sure you have `sqlite3` installed for your system. initialise a new instance of the database by running `sqlite3 your_db_name.sqlite < schema.sql`, and adding its full path as `DB_PATH` to `.env`.
- recommended: set up a `virtualenv`
- install all python dependencies: `pip install -r requirements.txt` 

### TO DO
new issues:
- we have a problem with parsing baggage options - for instance, jet blue basic economy only returns 4 list elements for price and baggage, which ends up with us losing these flight options entirely
- maybe we're not getting enough options? sometimes, we on;y have one airline. we want a bit more for that kind of stuff. maybe we can increase what we get somehow, in the sense of diversity of airlines? 

- test different journey options    
    - ~~test `multi_city` journeys~~
    - test `city_options` journeys
- add airport parsing
    - ~~add airport validation~~
    - ~~add distance calculation to journeys table~~
- look into what we need to do with the bridge tables 
  in the db
- ~~find stale element error, and effectively handle it~~
- look into socks5 proxies, implement into scraper
- ~~add typical script for search & adding to DB~~
- ~~write a script to add a search to crontab~~
- look at what happens if we run headless
- try working out a way to run headless with x11 server

### notes:
- website owners like to change the xpaths and css_selectors on their sites, in order to prevent scraping. so, you may have to re-locate the relevant elements and update them in `config.yaml` if something isn't working; especially if you're getting errors from `selenium` 
- on MacOS, your chromedriver executable may be 'quarantined' by the OS. you can un-quarantine it (at your own risk -- make sure to download the driver from the official source only) by running  `xattr -d com.apple.quarantine path/to/chromedriver`

### comparisons & acknowledgments
there are a bunch of existing projects hosted on github which aimed to solve a similar problem. i used some of them to get inspiration and a better understanding of how to approach this particular problem, and would like to thank the authors for sharing their code. specifically, these are:

- `https://github.com/fnneves/flight_scraper` 
- `https://github.com/amal-hasni/kayak_scraper` 
- `https://github.com/MeshalAlamr/flight-price-prediction`  