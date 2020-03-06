import os
from pathlib import Path
import functools
import logging
import logging.handlers
from _collections_abc import MutableMapping
import datetime
import re
import copy

numbers = [
    "zero", "one", "two", "three", "four", "five", "six", "seven"
    "eight", "nine", "ten", "eleven", "twelve", "thirteen", "fourteen"
    "fifteen", "sixteen", "seventeen", "eighteen", "nineteen", "twenty"
    ]
months = [
    "Jan.", "Feb.", "Mar.", "Apr.", "May.", "Jun.",
    "Jul.", "Aug.", "Sep.", "Oct.", "Nov.", "Dec."
    ]
states = [
    "A.L.", "A.K.", "A.Z.", "A.R.", "C.A.", "C.O.", "C.T.",
    "D.E.", "F.L.", "G.A.", "H.I.", "I.D.", "I.L.", "I.N.", "I.A.", "K.S.",
    "K.Y.", "L.A.", "M.E.", "M.D.", "M.A.", "M.I.", "M.N.", "M.S.", "M.O.",
    "M.T.", "N.E.", "N.V.", "N.H.", "N.J.", "N.M.", "N.Y.", "N.C.", "N.D.",
    "O.H.", "O.K.", "O.R.", "P.A.", "R.I.", "S.C.", "S.D.", "T.N.", "T.X.",
    "U.T.", "V.T.", "V.A.", "W.A.", "W.V.", "W.I.", "W.Y.",
    ]


def get_file_text(file_name):
    """Get text from file.

    Gets text from given file name whether the file is specified using
    pathlib.Path or a path string.
    """
    if isinstance(file_name, Path):
        text = file_name.read_text()
        return text
    if isinstance(file_name, str):
        with open(file_name, "r") as f:
            text=f.read()
        return text
    else:
        raise IOError("Incorrect file name")


def clean_to_dict(dirty, delimeter="\n"):
    """Clean provided string and enter into dict.

    Cleans unparsed information based first on delimeter (default newline),
    then on colon space. Fills a dict with the cleaned information. For use on
    header files derived from Mozilla Firefox.
    """
    clean_info = {}
    split_dirty = dirty.split(delimeter)
    for line in split_dirty:
        key_value = line.split(": ", 1)
        clean_info[key_value[0]] = key_value[1]
    return clean_info


def cd(path):
    """Decorate a function to run it in path and then return to start path

    Decorates a function to work with the ChangeDirManager without loss of
    indent space. Changes directory, runs the function, and then changes
    back to the original directory
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with ChangeDirManager(path):
                result = func(*args, **kwargs)
            return result
        return wrapper
    return decorator


class ChangeDirManager():
    """A context manager which safely changes directory and then returns"""
    def __init__(self, path, logger_level="DEBUG"):
        self.path = Path(path)
        self.logger = logging.getLogger(__name__)
        normalize_logger(self.logger, logger_level=logger_level)
        if not self.path.is_dir():
            self.logger.warning("Path is not a directory")
            raise IOError("Path is not directory")
        self.prev_path = Path.cwd()

    def __enter__(self):
        self.logger.debug(f"Moving to: {self.path}")
        os.chdir(self.path)

    def __exit__(self, *exc):
        self.logger.debug(f"Moving back to: {self.prev_path}")
        os.chdir(self.prev_path)


def normalize_logger(
                    logger,
                    logger_level="INFO",
                    stdout_handler=logging.StreamHandler(),
                    file_handler=logging.handlers.RotatingFileHandler,
                    log_format=logging.Formatter(
                        "{asctime} : {levelname} : {name} : {message}",
                        style="{"
                        ),
                    log_path = Path("./debug")
    ):
    """Formats logger to the standard I personally use (deprecated)"""
    for handle in logger.handlers:
        logger.removeHandler(handle)
    logger.setLevel(logger_level)

    if not stdout_handler.formatter:
        stdout_handler.setFormatter(log_format)
    if stdout_handler.level == 0:
        stdout_handler.setLevel("WARNING")

    if isinstance(file_handler, type):
        file_handler = file_handler(
                filename=log_path / Path(f"{logger.name}.log"),
                maxBytes=2097152,
                backupCount=5
                )
    if not file_handler.formatter:
        file_handler.setFormatter(log_format)
    if file_handler.level == 0:
        file_handler.setLevel(logger.level)

    logger.addHandler(stdout_handler)
    logger.addHandler(file_handler)


class TOML(dict):
    """Create a TOML object accessible through dot notation

    Creates a TOML object which acts like a dictionary in most capacities, but
    is accessible through dot notation (as in a TOML document) and allows for
    cleaner .get() notation. Attributes whose names collide with reserved
    functions are modified to start with an additional underscore. Accessing
    quoted TOML keys must be done through .get(), slicing[], or getattr().
    This class subclasses dict (instead of MutableMapping) in order to be read
    by certain TOML encoders.
    """

    def __init__(self, dikt):
        """Set key:value pairs as attributes of this object; dicts are recursed

        Transforms a dict into a TOML object by setting key:value pairs into
        attribute = value pairs. Any nested dicts are recursively transformed
        into TOML objects to make the TOML object fully accessible through dot
        notation. Keys which collide with reserved functions are prefixed
        with an underscore.
        """
        for key, value in dikt.items():
            if key in TOML.__dict__.keys():
                key = f"_{key}"
            try:
                setattr(self, key, TOML(value))
            except AttributeError:
                setattr(self, key, value)

    def __setitem__(self, key, value):
        setattr(self, key, value)

    def __delitem__(self, key):
        delattr(self, key)

    def __getitem__(self, key):
        return getattr(self, key)

    def __iter__(self):
        yield from self.asdict().items()

    def __len__(self):
        return len(self.asdict())

    def __repr__(self):
        return str(self.asdict())

    def __str__(self):
        return str(self.asdict())

    def __contains__(self, item):
        try:
            getattr(self, item)
            return True
        except AttributeError:
            return False

    def __eq__(self, other):
        try:
            if self.__dict__ == other.__dict__:
                return True
        except AttributeError:
            pass
        return False

    def clear(self):
        self.__dict__.clear()

    def update(self, *args, **kwargs):
        self.__dict__.update(*args, **kwargs)

    def pop(self, key):
        result = self.get(key)
        delattr(self, key)
        return result

    def copy(self):
        return TOML(self.asdict())

    def setdefault(self, key, default=None):
        try:
            return getattr(self, key)
        except AttributeError:
            setattr(self, key, default)
            return getattr(self, key)

    def fromkeys(self, keys, value=None):
        result_dict = dict.fromkeys(keys, value)
        return TOML(result_dict)

    def popitem(self):
        pop_key = list(self.keys())[-1]
        return self.pop(pop_key)

    def items(self):
        return self.asdict().items()

    def values(self):
        return self.asdict().values()

    def keys(self):
        return self.asdict().keys()

    def get(self, key, default=None):
        """Return value of specified key, or default if key DNE

        Retrieves value of specified key from this (and nested) TOML object(s).
        If key does not exist at any point, retrieves default instead (None by
        default). Intended as comparative to dict.get().
        """
        # pattern finds TOML keys (bare or quoted). Groups take advantage of
        # re.split returning groups it split on
        pattern = """(?:'([^']*)'(?:[.]?)|"([^"]*)"(?:[.]?)|([^.]*)(?:[.]?))"""
        splitter = re.compile(pattern)
        attributes = splitter.split(key)
        # attributes has many None or '' entries from how re splitting works
        attributes = [attr for attr in attributes if attr]
        result = self
        try:
            for attribute in attributes:
                result = getattr(result, attribute)
            return result
        except AttributeError:
            # print(e)
            return default

    def asdict(self):
        # result = copy.deepcopy(self.__dict__)
        # try:
        #     for key, value in result.items():
        #         if key.startswith()
        # except AttributeError:

        # return result
        return self.__dict__