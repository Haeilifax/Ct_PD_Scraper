"""Module for inserting data into databases"""
import sqlite3
import ast
import json
import re

from pathlib import Path
from abc import abstractmethod

from ct_pd_scraper import MySQLdbAdapter as mysqldb
from ct_pd_scraper.cleaner import clean_date


def get_date(file_name):
    """Obsolete method of getting date from a well-formed file-name"""
    pattern = r"[0-9]{4}-[0-9]{1,2}-[0-9]{1,2}"
    date = re.search(pattern, file_name).group()
    return date


def extract_data(data_file):
    """Obsolete method of getting data from file"""
    if not Path(data_file).is_file():
        raise IOError("File does not exist")
    if data_file.endswith(".txt"):
        text = data_file.read_text()
        data = ast.literal_eval(text)
    elif data_file.endswith(".json"):
        data = json.loads(data_file.read_text())
    else:
        raise TypeError("Expected file of type .txt or .json")
    return data


def get_inserter(variety, config, **kwargs):
    """Factory method for returning an inserter

    For SQLite inserter (SQLite databases), provide the path to a valid sqlite
    database file as the parameter "database".

    For MySQL inserter (MySQL database), provide the database to connect to and
    any necessary keyword parameters for the MySQLdb connection. Options are
    listed in mysqlclient documentation at:
        (https://mysqlclient.readthedocs.io/user_guide.html)
    """
    if (cased := variety.lower()) == "sqlite":
        return SQLiteInserter(config, **kwargs)
    if cased == "mysql":
        return MySQLInserter(config, **kwargs)
    raise TypeError("Please choose an appropriate database type")


class AbstractInserter:
    """Abstract inserter class

    Abstract inserter class containing context manager logic for opening and
    closing a connection and methods for inserting into a given database
    according to python's database interface.

    To subclass: override __init__ and database_connect.
    """

    @abstractmethod
    def __init__(self, config, **kwargs):
        self.config = config
        self.param_query_start = ""
        self.param_query_end = ""

    def __enter__(self):
        self.database_connect()
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.database_close()

    @abstractmethod
    def database_connect(self):
        pass

    def database_close(self):
        self.conn.close()

    def _insert_name(self, first_name, last_name):
        """Insert given first_ and last_ name into database.

        Insert first_name and last_name into self.database using parameterized
        queries. Formatted strings are used to allow inserters to specify
        their own parameterization marks (e.g. colon before for SQLite or
        %( before and )s after for MySQL). self.conn is not generated in
        __init__, using this method outside of the insert method may lead to
        unexpected behaviors.

        Args:
            first_name, last_name: first and last name to insert into database

        Returns:
            None
            Prints values (first_name, last_name) to stdout
            Sets self.p_id to the row id of the inserted name, for use in
            _insert_content
        """
        cur = self.conn.cursor()
        sql = """
        INSERT INTO person (first_name, last_name)
        VALUES ({0}first_name{1}, {0}last_name{1})
        """
        values = {"first_name": first_name, "last_name": last_name}
        print(values)
        cur.execute(sql.format(self.param_query_start, self.param_query_end), values)
        self.p_id = cur.lastrowid

    def _insert_content(self, content, pdcity="Unknown", date="Unknown"):
        """Insert content of blotters into database

        Insert content, pdcity, and date into self.database using
        parameterized queries. Formatted strings are used as in _insert_name.
        Using this method outside of the insert method will lead to
        unexpected behaviors. This method relies on self.p_id from
        _insert_name -- must only be used after it is set.

        Args:
            content: content of blotter to be inserted (str)
            pdcity: police department which made the arrests (str)
            date: date police blotter was posted (ISO date formatted str)

        Returns:
            None
            Prints values (self.p_id, content, date, pdcity) to stdout
        """
        cur = self.conn.cursor()
        sql = """
        INSERT INTO content (person_id, content, date, pdcity)
        VALUES ({0}person_id{1}, {0}content{1}, {0}date{1}, {0}pdcity{1})
        """
        values = {
            "person_id": self.p_id,
            "content": content,
            "date": date,
            "pdcity": pdcity,
        }
        print(values)
        cur.execute(sql.format(self.param_query_start, self.param_query_end), values)

    def insert(self, data, date=None, pdcity=None):
        """Governer for inserting values into database

        Master method for final cleaning of data and inserting into database.
        Ensures that self.conn is populated before attempting to insert.
        Ensures that data and pdcity were passed, either as arguments or
        as keys in data, and if not, populates them with default values. Cleans
        the date from the expected natural language format before inserting.

        Args:
            data: dictionary containing dictionaries as values for arbitrary
                keys. Nested dictionaries should contain keys "name" and
                "content", with string values (dict)
            date: Natural language date on which the blotters were posted.
                Should be of the format "Month Day, Year", e.g.
                "March 27, 2020". Day should be cardinal (27), not ordinal
                (27th).
            pdcity: Name of city where arrests happened

        Returns:
            None
            _insert_name and _insert_content print values to stdout
        """
        if not self.conn:
            raise Exception("Connect to a database")
        if not date:
            date = data.get("date", "0000-00-00")
            data.pop("date", None)
        date = clean_date(date)
        if not pdcity:
            pdcity = data.get("pd_city", "Unknown")
            data.pop("pd_city", None)
        with self.conn:
            for _, arrest in data.items():
                full_name = arrest["name"].split()
                first_name = " ".join(full_name[:-1])
                last_name = full_name[-1]
                content = arrest["content"]
                self._insert_name(first_name, last_name)
                self._insert_content(content, pdcity, date)


class SQLiteInserter(AbstractInserter):
    """Inserter for SQLite databases"""

    def __init__(self, config, **kwargs):
        """Initialize variables

        Initialize database path based first off given kwargs, then off config
        dict.

        Args:
            config: dictionary providing database configuration. Overridable
                with **kwargs. (dict)
                    Keys:
                    "data_path": path to data folder (folder containing
                        the database) (str or Path)
                    "sqlite": dictionary providing configuration details for
                        SQLite database. (dict)
                            Keys:
                            "database": database filename (str or Path)
            **kwargs: provided to override config. Provide any keyname to use
                **kwargs value instead
        """
        self.data_path = kwargs.get("data_path", config.get("data_path"))
        self.config = config.get("sqlite", {}).copy()  # Avoid contaminating config
        self.config.update(kwargs)
        self.database = self.config.get("database")
        self.param_query_start = ":"
        self.param_query_end = ""

    def database_connect(self):
        """Connects to database given by configuration. Errors if file DNE

        Raises:
            IOError: The database given does not exist
        """
        database_path = Path(self.data_path) / Path(self.database)
        if Path(database_path).is_file():
            try:
                conn = sqlite3.connect(database_path)
                self.conn = conn
            except sqlite3.Error as e:
                print(e)
        else:
            raise IOError("Database not found")


class MySQLInserter(AbstractInserter):
    """Inserter for MySQL databases"""

    def __init__(self, config, **kwargs):
        """Initialize variables

        Initialize configuration of database connection variables.

        Args:
            config: dictionary with configuration values for MySQL database
                connection under the key "mysql" (dict)
                    Keys:
                    "mysql": dict containing key-value pairs (dict)
                        Keys:
                        see:
                        https://mysqlclient.readthedocs.io/user_guide.html
                        for details
                        "host", "user", "password", "database", "port",
                        "unix_socket", "conv", "compress", "connect_timeout",
                        "named_pipe", "init_command", "read_default_group",
                        "cursorclass", "use_unicode", "charset", "sql_mode",
                        "ssl"
            **kwargs: Override any key-value in config["mysql"]
        """
        self.config = config.get(
            "mysql", {}
        ).copy()  # Don't contaminate original config
        self.config.update(kwargs)
        self.param_query_start = "%("
        self.param_query_end = ")s"

    def database_connect(self):
        self.conn = mysqldb.connect(**self.config)
