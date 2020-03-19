import json
import re
from time import sleep
from pathlib import Path
import logging
import traceback

import requests
from tqdm import tqdm
from bs4 import BeautifulSoup, SoupStrainer

from .scrape_police import login, scrape
from . import cleaner
from . import inserter
from . import settings
from . import exceptions


def get_links(session, config):
    print(f"Getting links to blotters from {config.base_url}...")
    info = session.get(config.base_url, headers=config.session_headers)
    link_strainer = SoupStrainer("a")
    soup = BeautifulSoup(info.content, "html.parser", parse_only=link_strainer)
    blotter = re.compile("blotter")
    links = soup.findAll(href=blotter, string=blotter)
    return links


def main():
    config = settings.SettingsObj("config.toml")

    with requests.Session() as session:
        print(f"Signing into {config.login_url}...")
        login(config.login_url, session, config.login_headers, config.log_info)

        links = get_links(session, config)

        link_file = config.data_path / config.link_file
        prev_links = settings.get_prev_links(link_file)

        new_links = [link["href"] for link in links if link["href"] not in prev_links]

        if new_links:
            print("New links available, scraping...")
        else:
            print("No new links available, exiting...")
            return

        insert = inserter.get_inserter(config.inserter_type, database=config.database)
        failed_scrapes = []
        try:
            for link in tqdm(new_links, ascii=True):
                try:
                    print("\nsleeping")
                    sleep(31)

                    print(f"Current link: {link}")

                    blot, date, pdcity = scrape(link, session, config.session_headers)

                    clean = cleaner.get_cleaner(config.cleaner_type)
                    clean_record = clean.clean_incidents(blot)
                    with insert:
                        insert.insert(clean_record, date=date, pdcity=pdcity)

                    prev_links.append(link)

                    print("Finished link")
                except Exception as e:
                    print(f"Scraping link {link} failed, due to:", str(e))
                    print(traceback.print_tb(e.__traceback__))
                    failed_scrapes.append((link, e))
        finally:
            with open(link_file, "w") as f:
                json.dump(prev_links, f)
        if failed_scrapes:
            print(f"Scrapes failed: {len(failed_scrapes)}")
            for pair in failed_scrapes:
                print(f"{pair[0]} due to {str(pair[1])},")
            raise exceptions.ScraperException
        print("COMPLETE")


if __name__ == "__main__":
    main()
