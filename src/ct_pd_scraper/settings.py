from pathlib import Path
import json

import tomlkit
import environs


class SettingsObj:
    def __init__(self, config_file):
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

        self.database = (
            self.data_path / Path(config.get("database.name", "pd.db"))
        ).resolve()
        self.inserter_type = config.get("database.inserter", "basic")
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
        except environs.EnvValidationError as e:
            print("Login information not found or incomplete")
            quit_prompt = input("Would you like to quit? (y/n) [y]")
            if not quit_prompt.lower().startswith("n"):
                raise e
            self.log_info = {}


def get_prev_links(link_file):
    if link_file.is_file():
        print("Previous link file found, opening...")
        with open(link_file, "r") as f:
            prev_links = json.load(f)
    else:
        print("Previous link file not found, creating new in memory...")
        prev_links = []
    return prev_links
