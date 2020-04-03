"""Main worker of script"""
import json
import re
from time import sleep
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
    """Get links to blotters from the base page

    Get links to police blotters on rep-am.com from the base page (default
    value https://www.rep-am.com/category/local/records/police/). Links are
    found using a BeautifulSoup search on every <a> tag for links which
    contain "blotter" in their href.

    Args:
        session: the current requests.Session (Session)
        config: a SettingsObj, usually generated off config.toml (SettingsObj)
            Properties:
            base_url: url to scrape links to blotters from
            session_headers: headers to mimic a human web browser

    Returns:
        links: list of links to blotters (list)
    """
    print(f"Getting links to blotters from {config.base_url}...")
    info = session.get(config.base_url, headers=config.session_headers)
    link_strainer = SoupStrainer("a")
    soup = BeautifulSoup(info.content, "html.parser", parse_only=link_strainer)
    blotter = re.compile("blotter")
    links = soup.findAll(href=blotter, string=blotter)
    return links


def main():
    """Scrapes blotters, cleans them, and inserts data into database

    This is the main method of this script. All input and modification can
    be done through a config.toml file located in the current working
    directory. This method creates and maintains a Session which is logged
    into rep-am.com. Links to blotters are scraped from the main page of the
    police news, and each blotter is then scraped for arrest records. These
    arrest records are cleaned of junk and inserted into the given database.
    Any errors in scraping, cleaning, or inserting are noted, and then
    continued around. Finally, all successfully scraped links urls are saved to
    the prev_links file to not be scraped again in the future. If no errors are
    raised, the program then quits. If there were errors during the process,
    the prompt remains open waiting for confirmation to close.

    Returns:
        None
        prints multiple times during the process

    Raises:
        ct_pd_scraper.exceptions.ScraperException: an exception occurred during
            the process. This is being raised so the prompt does not close
            automatically
    """

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

        insert = inserter.get_inserter(config.inserter_type, config=config.connconfig)
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
