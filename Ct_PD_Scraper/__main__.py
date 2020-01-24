import requests
import json
import re
from time import sleep
from random import randint
from pathlib import Path
import os
import logging
from threading import Timer

from tqdm import tqdm
from bs4 import BeautifulSoup, SoupStrainer
import qtoml
import environs

from .scrape_police import login, get_headers, get_log_info, scrape
from .useful import cd, ChangeDirManager, normalize_logger, TOML
from . import cleaner
from . import inserter


def main():
    # config_dict = qtoml.loads(Path("config.toml").read_text())
    # config = TOML(config_dict)
    # data_path = config.get("data.path", Path("../data"))
    # login_url = config.get("login.url", "https://www.rep-am.com/login")
    # env_path = config.get("env.dir", Path(".."))
    # with ChangeDirManager(env_path):
    #     env = environs.Env().read_env()
    data_path = Path("./data")
    logger = logging.getLogger(__name__)
    normalize_logger(logger)
    with requests.Session() as session:
        with ChangeDirManager(data_path):
            log_info = get_log_info()
            login_headers = get_headers("login_headersinfo.txt")
            headers = get_headers()
        login_url = "https://www.rep-am.com/login"
        print(f"Signing into {login_url}...")
        login(login_url, session, login_headers, log_info)
        base_url = "https://www.rep-am.com/category/local/records/police/"
        print(f"Getting links to blotters from {base_url}...")
        info = session.get(base_url, headers = headers)
        link_strainer = SoupStrainer("a")
        soup = BeautifulSoup(
            info.content, "html.parser", parse_only=link_strainer
            )
        blotter = re.compile("blotter")
        links = soup.findAll(href=blotter, string=blotter)
        logger.info(f"Found links, first three: {links[:3]}")
        logger.debug(f"all links: {links}")
        with ChangeDirManager(data_path):
            link_file = Path("scraped_links.json")
            if link_file.is_file():
                logger.info("prev_link file found")
                print("Previous link file found, opening...")
                with open(link_file, "r") as f:
                    prev_links = json.load(f)
            else:
                logger.info("prev_link file not found")
                print("Previous link file not found, creating new in memory...")
                prev_links = []
        logger.debug(f"prev_links currently: {prev_links}")
        new_links = [
            link["href"] for link in links if link["href"] not in prev_links
            ]
        logger.debug(f"all new links found: {new_links}")
        logger.info(f"Found new links, first 3: {new_links[:3]}")
        if new_links:
            print("New links available, scraping...")
        # wait_timer = Timer(30.5, scrape)
        insert = inserter.get_inserter("basic", database=data_path/"pd.db")
        for link in tqdm(new_links, ascii=True):
            logger.info("sleeping")
            print("\nsleeping")
            sleep(31)
            logger.info(f"Current link: {link}")
            print(f"Current link: {link}")
            blot, date = scrape(link, session, headers)
            logger.debug(f"content scraped from {link}: {blot}")
            logger.info("Entering cleaning")
            clean = cleaner.get_cleaner("basic")
            clean_record = clean.clean_incidents(blot)
            with insert:
                insert.insert(clean_record, date=date)
            prev_links.append(link)
            logger.info(f"prev_links now: {prev_links}")
            print("Finished link")
        with ChangeDirManager(data_path):
            logger.debug(f"opening file {link_file}")
            with open(link_file, "w") as f:
                logger.info(f"Dumping list of scraped links into {link_file}")
                json.dump(prev_links, f)
        print("COMPLETE")
        logger.info("COMPLETE")


if __name__ == "__main__":
    main()