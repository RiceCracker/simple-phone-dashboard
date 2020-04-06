# Simple Phone Dashboard
A simple flask based RESTful API and dashboard to display common phone data crawled from phone web interfaces on a web frontend.

# Introduction
This project crawls data from phones which support web interfaces supporting http-auth. The code is splitted into a RESTful API  (based on [Miguel Grinberg's RESTful Authentication with Flask tutorial](https://blog.miguelgrinberg.com/post/restful-authentication-with-flask) written in Flask handling the phone database and a dasboard based on [CreativeTim's argon-dashboard](https://github.com/creativetimofficial/argon-dashboard). 

Please keep in mind that this project is far from finished and is still work in progress and not optimized for production environments yet. There is no warranty provided.

# How it works
## About phones
Before talking about the procedure, I want to mention that this project was primarily built around SNOM D725 phones, but should work with any phone that supports web interfaces. To achieve this some customization in modules/data.py is needed to differentiate phone types and crawl their respective interfaces. 

## On database creation and API login
The database will be automatically created by flask-mysqlalchemy and the defined database models, so if you want to modify the database you should do so in these. Custom PRAGMA keys can be defined while database initialization.

The API login can be set by sending a request to the API on first run, sending a curl request:
```
curl -i -X POST -H "Content-Type: application/json" -d '{"username":"username","password":"password"}' 
http://127.0.0.1:5000/api/users
```
## On crawling phone data and writing to database
Upon running, the API will try to reach the phone web interfaces definded in devices.py and log onto them, if successful. In consequence the beautifulsoup4 library is used to extract the data (missed, received, dialed calls) from the main page using the data module in which custom crawling procedures for different phones can be defined if needed. The API will write the resulting datasets to the database, skipping existing entries. 

## On retrieving the data using the RESTful API
The API has the ability to make use of either mysqlalchemy objects or execute SQL statements which can be copied into /sql and executed using the data.read_sql command. The current API resources include several functions to retrieve phone information as well as call information.

## On using the dashboard to display data
CreativeTim's Argon Dashboard provides a Flask branch which is used in combination with the Flask API. The API-retrieved data is displayed in either graphs or tables depending on your needs. As there is no real manual for the dashboard you will have to figure out most things yourself. This implementations usage of the Flask RESTful API does not make use of java-script calls to retrieve the data, hence the implementation using HTML template code. If you want to implement graphs using java-script, you will need to modify /app/static/assets/js/argon.js to log into the api first. Any other modifications should happen in the HTML templates as well as the dashboard's view.py.

## On configuration
The configuration of both API and dashboard can be achieved by modifying their respective config.py and configuration.py files.

## On virtual environments
Before anything can be run, [virtual environments have to be set up for API and Argon Dashboard](https://github.com/app-generator/flask-argon-dashboard).
