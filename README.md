# flight_prices_trends
flight prices change, sometimes unpredictably. this software will let you track the price and availability of very flexibly defined routes over time. 

Last updated: NL, 17/12/23

### tl, dr
`flight_prices_trends` is a software that aims to help illuminate the mistery of flight prices, allowing you to track trends over a long period of time. 

At its core, the software incorporates a scraper for the skyscanner flight price comparison website, functionality for performing several, recurring scraper calls from different IP addresses via socks5 proxies (to avoid banning), a lean SQLite database to store the data, and some analytics to provide interpretation on what's going on with prices. 


### TO DO
1. scraper
- ~~can we do it with only requests? or do we need to use beautiful soup? ~~ --> we need beautiful soup or selenium.
- what are the various categories? 
    - one-way
    - return
    - multi-city
- what does the data look like, how to parse
    - stops
    - time
    - airline(s)
    - price


0. future nice-haves:
- ensure any free-text input resolves to an IATA airport code or fails
- allow different start and return points (multi-city)



### NOTES:
- you will need to install chromedriver. you will need to add the full path to it as `CHROMEDRIVER` in your `.env` file. 
- you also need to ensure that the version of your chromedriver exeutable matches the version of chrome you have installed on your machine. if you do not have chrome installed on your machine, you will have to install it. 
- on MacOS, your chromedriver executable may be 'quarantined' by the OS. you can un-quarantine it (at your own risk -- make sure to download the driver from the official source only) by running  `xattr -d com.apple.quarantine path/to/chromedriver`


### COMPARISONS
- `https://github.com/fnneves/flight_scraper` -- not particularly good or clean code - a lot of long sleeping without it being clear when it's doing so and for how long. page elements no longer work, so pretty useless for our purpose. 
- `https://github.com/amal-hasni/kayak_scraper` -- 
- `https://github.com/MeshalAlamr/flight-price-prediction` -- the base code is a bit weak and not robust to errors, doesn't adhere to a lot of principles. moreover, the xpath elements/divs for the relevant data are no longer up to date. 