"""Data cleaner for ct_pd_scraper"""

import ast
import json


MONTHS = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
]


def get_cleaner(variety, **kwargs):
    """Factory method for returning appropriate cleaner

    Args:
        variety: currently nothing - intended as selecter flag (str)
        **kwargs: any further arguments for the cleaner

    Returns:
        The cleaner specified
    """
    # if (variety.lower()) == "basic":
    #     return Basic_Cleaner(**kwargs)
    # elif cased == "testing":
    #     return Cleaner(**kwargs)
    return BasicCleaner(**kwargs)


def get_dirty_incident(file_name):
    """Method of getting police blotters from either text or json file"""
    if file_name.endswith(".json"):
        with open(file_name, "r") as f:
            dirty_incident = json.load(f)
    elif file_name.endswith(".txt"):
        with open(file_name, "r") as f:
            dirty_incident = f.read()
            dirty_incident = ast.literal_eval(dirty_incident)
    else:
        raise IOError("Expected .json or .txt")
    return dirty_incident


def get_arrests(dirty_incidents):
    """Extract only the arrest records from a scraped blotter

    Extract only the arrest records from a scraped blotter. This technique also
    extracts any all-caps fields (Occasionally blotters start with "POLICE
    BLOTTER", or etc.) -- these are removed later in the process.

    Args:
        dirty_incidents: list of records from scrape_police.scrape() (list)

    Returns:
        arrests: list of non-junk records. May still contain certain
            non-content records. (list)
    """
    arrests = []
    for phrase in dirty_incidents:
        try:
            if phrase.split(", ")[0].isupper():
                arrests.append(phrase)
        except Exception:
            continue
    return arrests


def clean_date(natural_date):
    """Transform a natural language date into an isoformat date

    Transform a date ("March 27, 2020") into an isoformat date ("2020-3-27").

    Args:
        natural_date: a naturally written date with only cardinal numbers, not
            ordinal numbers
                Yes: "March 27, 2020"
                No: "March 27th, 2020"

    Returns:
        isodate: date formatted to ISO specifications in the format
            YYYY-MM-DD. Returns "0000-00-00" if something is wrong.
    """
    try:
        *rest, year = natural_date.rsplit(", ")
        month_str, day = rest[0].split()
        month = str(MONTHS.index(month_str) + 1)
        isodate = "-".join([year, month, day])
    except Exception as e:
        print("Date failed due to:", e)
        isodate = "0000-00-00"
    return isodate


class BasicCleaner:
    """Clean a given blotter for insertion into a database"""

    def __init__(self):
        self.incidents = {}

    def clean_incidents(self, dirty_incident):
        """Clean given blotter

        Clean a given blotter based on the first comma. Make and return a
        dictionary with keys given by indices, and the values of those keys
        being dictionaries containing the keys name and content. The values
        of those keys are, respectively, the name of the arrested individual
        and the non-name content of the arrest record.

        Args:
            dirty_incident: list of records from scrape_police.scrape() (list)

        Returns:
            self.incidents: a dictionary of cleaned records -- any malformed
                records are removed as well.
        """
        arrests = get_arrests(dirty_incident)
        for index, phrase in enumerate(arrests):
            current_arrest = phrase.split(", ", 1)
            self.incidents[index] = {}
            try:
                self.incidents[index]["name"] = current_arrest[0]
                self.incidents[index]["content"] = current_arrest[1]
            except IndexError:
                self.incidents.pop(index, None)
                continue
        return self.incidents
