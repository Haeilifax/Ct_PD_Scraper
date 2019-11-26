import os
import ast
import argparse

def get_dirty_incidents(file_name):
    with open(file_name, "r") as f:
        dirty_incidents = f.read()

    return dirty_incidents


def clean_incidents(dirty_incident):
    incidents = {}
    i = 0
    order = ["name", "age", "address"]
    dirty_incident_list = ast.literal_eval(dirty_incident)
    numbers = [
        "zero", "one", "two", "three", "four", "five", "six", "seven"
        "eight", "nine", "ten", "eleven", "twelve", "thirteen", "fourteen"
        "fifteen", "sixteen", "seventeen", "eighteen", "nineteen", "twenty"]
    months = [
        "Jan", "Feb", "Mar", "Apr", "May", "Jun",
        "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    for phrase in dirty_incident_list:
        if phrase == "":
            pass
        elif not phrase[1].isupper():
            pd_city = phrase[0]
        elif not "," in phrase:
            pass
        elif phrase.startswith("Logged in as"):
            break
        else:
            print(phrase)
            current_arrest = phrase.split(", ", 3)
            incidents[i] = {k: v for k, v in zip(order, current_arrest[0:3])}
            if incidents[i]["address"].startswith("of "):
                incidents[i]["address"] = incidents[i]["address"][3:]
            current_arrest_dangle = current_arrest[-1].split(', ')
            # Append city name to address if it's present
            if current_arrest_dangle[0][0].isupper():
                incidents[i]["address"]=", ".join([
                    incidents[i]["address"], 
                    current_arrest_dangle.pop(0)
                        ])
            clean_crimes = []
            # List crimes with their counts in integer form
            for crime in current_arrest_dangle:
                if crime.split()[0] in numbers:
                    crime = crime.split(" counts of ")
                    crime[0] = numbers.index(crime[0])
                    clean_crimes.append(crime)
                elif crime.split() in months:
                    period_delim = crime.split
                    incidents[i]["date"]

                else:
                    crime = [1, crime]
                    clean_crimes.append(crime)
            incidents[i]["crimes"] = clean_crimes
            i += 1
    return incidents, pd_city

def main(dirty_file):
    new_file = f"clean_{dirty_file}"
    with open(new_file, "w") as f:
        cleaned = clean_incidents(get_dirty_incidents(dirty_file))
        incidents, pd_city = cleaned
        f.write(incidents)  # If this broke, you probably need to stringify
        f.write(f"#{pd_city}")
    return new_file

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description = "Clean a file")
    parser.add_argument(
        "file",
        help="file path we want to clean"
    )
    args = parser.parse_args()
    main(args.file)
    with open(f"clean_{args.file}", "w") as f:
        cleaned = clean_incidents(get_dirty_incidents(args.file))
        incidents, pd_city = cleaned
        f.write(incidents)  # If this broke, you probably need to stringify
        f.write(f"#{pd_city}")