# -*- coding: utf-8 -*-
import os
import pathlib
import datetime
import requests
import copy as copy
from requests.auth import HTTPDigestAuth
from requests.auth import HTTPBasicAuth
from bs4 import BeautifulSoup
import config

# Get content from Web Page
def get(url):
    path  = config.SSL + "://" + url
    connerror = None

    try:
        response = requests.get(path, auth=HTTPDigestAuth(config.AUTH_USER, config.AUTH_PASS))
        if "Unauthorized" in response.text:
            print("Authtype 'digest' failed with:", response, response.text[:-2], "\nRetry with 'basic' auth...")

            response = requests.get(path, auth=HTTPBasicAuth(config.AUTH_USER, config.AUTH_PASS))
            if "Unauthorized" in response.text:
                print("Authtype 'basic' failed with:", response, response.text[:-2], "\nExiting...")

    except Exception as e:
        connerror = str(e)

    if connerror != None:
        print("Request to", url, "yielded:", "<Response [400]>")
        print("\nConnection failed with the following error:\n-\n" + connerror + "\n-\nIs the phone connected to the network?\n")
        return None

    else:
        print("Request to", url, "yielded:", response)
        return response

# Parse call data from HTML
def parse_html(url, verbose=False):
    # initialize call types and dataset
    calls = {"list_dialed":[], "list_missed":[], "list_received":[]}

    # Parse calls from markup
    html = get(url)
    if html == None:
        return

    soup = BeautifulSoup(html.content, "lxml")
    soup = soup.select("table")

    for table_layer0 in soup:
        for table_layer1 in table_layer0.findChildren("table"):
            for table_layer2 in table_layer1.findChildren("table"):

                # Check if child contains calls and note down type
                typecheck = [False, None]
                for type in calls:
                    typecheck = [True, type] if type in str(table_layer2) else typecheck
                if not typecheck[0]:
                    continue

                # Preprocess call data and clean up
                table_layer2 = table_layer2.findAll("tr")

                # Get call data
                for tr in table_layer2[2:]:
                    data = []
                    for td in tr.findAll("td"):
                        if len(td.text) != 0:
                            a = td("a")
                            if a != []:
                                tags = []
                                for tag in a:
                                    if len(tag.text.replace(" ", "")) != 0:
                                        tags.append(tag.text)
                                        data += tags
                                        tag.extract()
                                data.append(td.text.replace(" ", ""))
                            else:
                                data.append(td.text.replace(" ", ""))

                    # print(data)
                    # Reformat Time
                    data[0] = datetime.datetime.strptime(data[0] + "T" + data[1], '%d.%m.%YT%H:%M').strftime('%Y-%m-%d %H:%M')
                    data.pop(1)

                    # Add data to dataset
                    calls[typecheck[1]].append(data)

            break

    # Print parsing results
    if verbose:
        print("----------------------------")
        print("Call record from:", url)
        for type in calls:
            print("\n", type)
            for call in calls[type]:
                print(call)

    # Return call data
    return calls

# Log Phone Data to DB
def parse_to_DB(phone_ip, database, verbose=False):
    print("\n---------------------")
    print("Get records from " + phone_ip + "...")

    record = parse_html(phone_ip, verbose)

    return record

# read SQL from file:
def read_sql(filename):
    filepath = os.path.join(pathlib.Path(os.path.dirname(os.path.realpath(__file__))).parent, "sql", filename)
    data     = None

    with open(filepath, 'r') as file:
        data = file.read()
    return data
