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


logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler)

def main():
    try:
        config_dict = qtoml.loads(Path("config.toml").read_text())
    except FileNotFoundError:
        config_dict = {}

    config = TOML(config_dict)

    data_path = Path(config.get("data.path", "./data")).resolve()

    login_url = config.get("login.url", "https://www.rep-am.com/login")
    login_headers = config.get("login.headers")
    session_headers = config.get("session.headers")
    base_url = config.get(
        "session.base_url",
        "https://www.rep-am.com/category/local/records/police/"
        )

    database = (data_path / Path(config.get("database.name", "pd.db"))).resolve()
    inserter_type = config.get("database.inserter", "basic")
    cleaner_type = config.get("cleaning.cleaner", "basic")

    env_path = Path(config.get("env.path", Path("."))).resolve()

    env = environs.Env()
    env.read_env(env_path / Path(".env"))
    try:
        log_info = {
            "log" : env.str("log"),
            "pwd" : env.str("pwd"),
            "submit" : env.str("submit"),
            "redirect_to" : env.str("redirect_to"),
            "testcookie" : env.str("testcookie")
        }
    except environs.EnvValidationError as e:
        print("Login information not found or incomplete")
        quit_prompt = input("Would you like to quit? (y/n) [n]")
        if quit_prompt.lower().startswith("y"):
            raise e
        log_info = {}


    with requests.Session() as session:
        print(f"Signing into {login_url}...")
        login(login_url, session, login_headers, log_info)
        print(f"Getting links to blotters from {base_url}...")
        info = session.get(base_url, headers = session_headers)
        link_strainer = SoupStrainer("a")
        soup = BeautifulSoup(
            info.content, "html.parser", parse_only=link_strainer
            )
        blotter = re.compile("blotter")
        links = soup.findAll(href=blotter, string=blotter)
        logger.info(f"Found links, first three: {links[:3]}")
        logger.debug(f"all links: {links}")

        link_file = data_path / Path("scraped_links.json")
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
        else:
            print("No new links available, exiting...")
            return
        # wait_timer = Timer(30.5, scrape)
        insert = inserter.get_inserter(inserter_type, database=database)
        try:
            for link in tqdm(new_links, ascii=True):
                logger.info("sleeping")
                print("\nsleeping")
                sleep(31)
                logger.info(f"Current link: {link}")
                print(f"Current link: {link}")
                blot, date, pdcity = scrape(link, session, session_headers)
                logger.debug(f"content scraped from {link}: {blot}")
                logger.info("Entering cleaning")
                clean = cleaner.get_cleaner(cleaner_type)
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