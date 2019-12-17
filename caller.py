import os
from bs4 import BeautifulSoup, SoupStrainer
import requests
import argparse
import sys
import json
import re
from time import sleep
from random import randint
from tqdm import tqdm

from scrape_police import login, get_headers, get_log_info, scrape
from useful import get_file_text
import cleaner
import inserter

if __name__ == "__main__":
    link_file = "scraped_links.json"
    with requests.Session() as session:
        log_info = get_log_info()
        login_headers = get_headers("login_headersinfo.txt")
        login_url = "https://www.rep-am.com/login"
        login(login_url, session, login_headers, log_info)
        base_url = "https://www.rep-am.com/category/local/records/police/"
        headers = get_headers()
        info = session.get(base_url, headers = headers)
        link_strainer = SoupStrainer("a")
        soup = BeautifulSoup(
            info.content, "html.parser", parse_only=link_strainer
            )
        blotter = re.compile("blotter")
        links = soup.findAll(href=blotter, string=blotter)
        with open(link_file, "rb") as f:
            prev_links = json.load(f)
        links = [link for link in links if link not in prev_links]
        print(links)
        blot = []
        for link in tqdm(links, ascii=True):
            print("sleeping")
            sleep(randint(31, 45))
            # print(link)
            debug = scrape(link["href"], session, headers)
            # print(debug)
            blot.append(debug)
            prev_links.append(link)
        print("finished scraping, now to clean")
        with open(link_file, "rb") as f:
            json.dump(prev_links, f)
        # with open("debug_blotter.log", "w") as f:
        #     f.write(str(blot))
        cleaned = []
        for record in blot:
            # print(record)
            clean = cleaner.get_cleaner("basic")
            cleaned.append(clean.clean_incidents(record))
        # with open("debug_cleaner.log", "w") as f:
        #     f.write(str(cleaned))
        with inserter.get_inserter("basic", database="toy.db") as insert:
            for incident in cleaned:
                insert.insert(incident)