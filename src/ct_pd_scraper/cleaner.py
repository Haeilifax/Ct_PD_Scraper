import ast
import argparse
import json
import logging
import re
import copy
from pathlib import Path
from abc import ABC

from .useful import numbers, states, months

logger = logging.getLogger(__name__)
stdout_handler = logging.StreamHandler()
stdout_handler.setLevel("WARNING")
log_format = logging.Formatter(
    "{asctime} : {levelname} : {name} : {message}",
    style="{"
    )
stdout_handler.setFormatter(log_format)
logger.addHandler(logging.NullHandler)
logger.addHandler(stdout_handler)


def get_cleaner(variety, **kwargs):
    if (cased:=variety.lower()) == "basic":
        return Basic_Cleaner(**kwargs)
    elif cased == "testing":
        return Cleaner(**kwargs)


def get_dirty_incident(file_name):
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


def clean_trailing_starting(text):
    text = text.strip()
    if text.startswith("of "): text = text[3:]
    text = text.strip(".")
    text = text.strip("()")
    return text


class AbstractCleaner(ABC):

    def __init__(self):
        self.incidents = {}


    #refactor to make standalone?
    #refactor into multiple methods to remove if/elif/else?
    def get_arrests(self, dirty_incident):
        arrests = copy.copy(dirty_incident)
        # print(arrests)
        for phrase in dirty_incident:
            # print(phrase, not "," in phrase)
            if phrase == "":
                # print(f"{phrase} is skipped")
                arrests.remove(phrase)
                # print(arrests)
            elif phrase.startswith("Date_posted"):
                self.incidents["date"] = phrase[13:]
                arrests.remove(phrase)
            elif phrase.startswith("Logged in as"):
                # print(f"{phrase} breaks loop")
                breaker = arrests.index(phrase)
                arrests = arrests[:breaker]
                # print(arrests)
                break
            elif phrase[1].islower():
                # print(f"{phrase} is a pd_city")
                self.incidents["pd_city"] = phrase.split()[0]
                arrests.remove(phrase)
                # print(arrests)
            elif not "," in phrase:
                # print(f"{phrase} is skipped")
                arrests.remove(phrase)
                # print(arrests)
        return arrests

class Basic_Cleaner(AbstractCleaner):

    def clean_incidents(self, dirty_incident):
        arrests = self.get_arrests(dirty_incident)
        for index, phrase in enumerate(arrests):
            try:
                current_arrest = phrase.split(", ", 1)
                logger.debug(current_arrest)
                self.incidents[index] = {}
                self.incidents[index]["name"] = current_arrest[0]
                self.incidents[index]["content"] = current_arrest[1]
            except Exception:
                logger.exception(f'\nIssue with phrase "{phrase}"')
                input("Continue...")
        return self.incidents

#DO NOT USE
#BROKEN
class Cleaner(AbstractCleaner):
    order = ["name", "age", "address"]

    def clean_incidents(self, dirty_incident):
        arrests = self.get_arrests(dirty_incident)
        for index, phrase in enumerate(arrests):
            try:
                print(f"{phrase} is an arrest")
                current_arrest = phrase.split(", ", 3)
                self.incidents[index] = {k: v for k, v in zip(Cleaner.order, current_arrest[0:3])}
                self.incidents[index]["address"] = clean_trailing_starting(self.incidents[index]["address"])
                current_arrest_dangle = current_arrest[-1].split(', ')
                # Append city name to address if it's present
                if current_arrest_dangle[0][0].isupper():
                    self.incidents[index]["address"]=", ".join([
                        self.incidents[index]["address"],
                        current_arrest_dangle.pop(0)
                            ])
                clean_crimes = []
                print(current_arrest_dangle)
                for crime in current_arrest_dangle:
                    print(crime)
                    #Make this a function
                    #Only keeping first word of crime; this likely broke
                    #refactor into multiple functions
                    if count := re.search("counts", crime):
                        indexed_crime = crime.split()
                        indexed_crime = [clean_trailing_starting(item) for item in indexed_crime]
                        count_index = indexed_crime.index(count.group())
                        number_offenses = indexed_crime[count_index - 1]
                        crime = re.sub(count.group(), "", crime)
                        crime = re.sub(number_offenses, "", crime)
                        crime = re.sub("[()]", "", crime)
                        crime = clean_trailing_starting(crime)
                        crime = [numbers.index(number_offenses), crime]
                        clean_crimes.append(crime)
                    elif (determinant:=crime.split()[0]) in numbers:
                        crime = crime.split(" counts of ")
                        crime[0] = numbers.index(crime[0])
                        clean_crimes.append(crime)
                    elif determinant in months:
                        date_notes = crime.split(". ")
                        self.incidents[index]["date"] = " ".join(date_notes[:2])
                        if len(date_notes) > 2:
                            self.incidents[index]["notes"] = "".join(date_notes[2:])
                    elif (determinant:=crime.split()[0]) in states:
                        self.incidents[index]["address"] = ", ".join([
                            self.incidents[index]["address"],
                            determinant])
                    else:
                        crime = [1, crime]
                        clean_crimes.append(crime)
                self.incidents[index]["crimes"] = clean_crimes
            except Exception:
                logger.exception(f'\nIssue with phrase "{phrase}"')
        return self.incidents


def main(dirty_file):
    file_name = dirty_file.rsplit(".", 1)[0]
    with open(new_file := f"clean_{file_name}.json", "w") as f:
        cleaner = Cleaner()
        incidents = cleaner.clean_incidents(get_dirty_incident(dirty_file))
        json.dump(incidents, f)
    return new_file


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description = "Clean a file")
    parser.add_argument(
        "file",
        help="file path we want to clean"
    )
    args = parser.parse_args()
    main(args.file)