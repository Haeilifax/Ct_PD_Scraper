"""Pre-scrape settings for ct_pd_scrape

NOTE: THIS MODULE RELIES ON A FORK OF TOMLKIT, FOUND AT
    https://github.com/Haeilifax/tomlkit_fluent.git
"""
from pathlib import Path
import json

import environs

import tomlkit_fluent as tomlkit


class SettingsObj:
    """Configuration object for ct_pd_scrape settings"""

    def __init__(self, config_file):
        """Creates an object with properties for configuration of scraper

        Initializes properties for a configuration object that will be used
        in setting up the scraper and modifying run-time execution without
        use of a commandline interface or modification of source code.

        Args:
            config_file: path to a TOML configuration file

        Raises:
            environs.EnvValidationError: if the .env file is incorrectly or
                not setup, offer opportunity to quit execution and raise
                error.
        """
        try:
            config = tomlkit.loads(Path(config_file).read_text())
        except FileNotFoundError:
            config = {}

        self.data_path = Path(config.get("data.path", "./data")).resolve()

        self.link_file = Path(
            config.get("prev_links.link_file", "scraped_links.json")
        ).resolve()

        self.login_url = config.get("login.url", "https://www.rep-am.com/login")
        self.login_headers = config.get("login.headers")
        self.session_headers = config.get("session.headers")
        self.base_url = config.get(
            "session.base_url", "https://www.rep-am.com/category/local/records/police/"
        )

        self.connconfig = dict(config.get("database.config", {}))
        self.connconfig.update({"data_path": self.data_path})
        self.inserter_type = config.get("database.inserter", "sqlite")
        self.cleaner_type = config.get("cleaning.cleaner", "basic")

        env_path = Path(config.get("env.path", Path("."))).resolve()

        env = environs.Env()
        env.read_env(env_path / Path(".env"))
        try:
            self.log_info = {
                "log": env.str("log"),
                "pwd": env.str("pwd"),
                "submit": env.str("submit"),
                "redirect_to": env.str("redirect_to"),
                "testcookie": env.str("testcookie"),
            }
        except environs.EnvValidationError as env_error:
            print("Login information not found or incomplete")
            quit_prompt = input("Would you like to quit? (y/n) [y]")
            if not quit_prompt.lower().startswith("n"):
                raise env_error
            self.log_info = {}


def get_prev_links(link_file):
    """Get previously scraped links from json link file

    Get list of previously scraped links from the given json link_file. If this
    file does not exist, create a new list in memory.

    Args:
        link_file: path to link file (Path or str)

    Returns:
        prev_links: list of links from file, or empty list if no file (list)
    """
    if Path(link_file).is_file():
        print("Previous link file found, opening...")
        with open(link_file, "r") as f:
            prev_links = json.load(f)
    else:
        print("Previous link file not found, creating new in memory...")
        prev_links = []
    return prev_links
