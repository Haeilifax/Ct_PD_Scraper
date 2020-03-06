import json
import re
from time import sleep
from random import randint
from pathlib import Path
import os
import logging
# from threading import Timer

import requests
from tqdm import tqdm
from bs4 import BeautifulSoup, SoupStrainer
import tomlkit
import environs

from .scrape_police import login, get_headers, get_log_info, scrape
from .useful import TOML
from . import cleaner
from . import inserter


logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler)


class _Settings():
    def __init__(self, config_file):
        try:
            config_dict = tomlkit.loads(Path(config_file).read_text())
        except FileNotFoundError:
            config_dict = {}

        config = TOML(config_dict)

        self.data_path = Path(config.get("data.path", "./data")).resolve()

        self.login_url = config.get("login.url", "https://www.rep-am.com/login")
        self.login_headers = config.get("login.headers")
        self.session_headers = config.get("session.headers")
        self.base_url = config.get(
            "session.base_url",
            "https://www.rep-am.com/category/local/records/police/"
            )

        self.database = (
            self.data_path
            / Path(config.get("database.name", "pd.db"))
            ).resolve()
        self.inserter_type = config.get("database.inserter", "basic")
        self.cleaner_type = config.get("cleaning.cleaner", "basic")

        env_path = Path(config.get("env.path", Path("."))).resolve()

        env = environs.Env()
        env.read_env(env_path / Path(".env"))
        try:
            self.log_info = {
                "log" : env.str("log"),
                "pwd" : env.str("pwd"),
                "submit" : env.str("submit"),
                "redirect_to" : env.str("redirect_to"),
                "testcookie" : env.str("testcookie")
            }
        except environs.EnvValidationError as e:
            print("Login information not found or incomplete")
            quit_prompt = input("Would you like to quit? (y/n) [y]")
            if not quit_prompt.lower().startswith("n"):
                raise e
            self.log_info = {}

def get_links(session, config):
    print(f"Getting links to blotters from {config.base_url}...")
    info = session.get(config.base_url, headers = config.session_headers)
    link_strainer = SoupStrainer("a")
    soup = BeautifulSoup(
        info.content, "html.parser", parse_only=link_strainer
        )
    blotter = re.compile("blotter")
    links = soup.findAll(href=blotter, string=blotter)
    logger.info(f"Found links, first three: {links[:3]}")
    logger.debug(f"all links: {links}")
    return links

def get_prev_links(link_file):
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
    return prev_links


def main():
    config = _Settings("config.toml")

    with requests.Session() as session:
        print(f"Signing into {config.login_url}...")
        login(config.login_url, session, config.login_headers, config.log_info)

        links = get_links(session, config)

        link_file = config.data_path / Path("scraped_links.json")
        prev_links = get_prev_links(link_file)

        new_links = [
            link["href"] for link in links if link["href"] not in prev_links
            ]
        logger.info(f"Found new links, first 3: {new_links[:3]}")
        logger.debug(f"all new links found: {new_links}")

        if new_links:
            print("New links available, scraping...")
        else:
            print("No new links available, exiting...")
            return

        # wait_timer = Timer(30.5, scrape)
        insert = inserter.get_inserter(config.inserter_type,
                                       database=config.database)
        try:
            for link in tqdm(new_links, ascii=True):
                logger.info("sleeping")
                print("\nsleeping")
                sleep(31)

                logger.info(f"Current link: {link}")
                print(f"Current link: {link}")

                blot, date, pdcity = scrape(link,
                                            session,
                                            config.session_headers)
                logger.debug(f"content scraped from {link}: {blot}")

                logger.info("Entering cleaning")
                clean = cleaner.get_cleaner(config.cleaner_type)
                clean_record = clean.clean_incidents(blot)

                with insert:
                    insert.insert(clean_record, date=date, pdcity=pdcity)

                prev_links.append(link)
                logger.info(f"prev_links now: {prev_links}")

                print("Finished link")
        finally:
            logger.debug(f"opening file {link_file}")
            with open(link_file, "w") as f:
                logger.info(f"Dumping list of scraped links into {link_file}")
                json.dump(prev_links, f)

        print("COMPLETE")
        logger.info("COMPLETE")


if __name__ == "__main__":
    main()