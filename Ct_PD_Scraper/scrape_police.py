import requests
import sys
import json
from pathlib import Path

from bs4 import BeautifulSoup

from .useful import get_file_text, clean_to_dict, ChangeDirManager


def login(url, session, headers = {}, log_info = {}):
    """Log into url using POST.

    Logs into a site on the web given by url, using provided login information
    and headers through POST method. The session is maintained.
    """
    try:
        response = session.post(url, data=log_info, headers = headers)
    except requests.RequestException as rex:
        print(str(rex))
    else:
        return response


def get_headers(header_file=Path("headersinfo.txt")):
    file_text = get_file_text(header_file)
    headers = clean_to_dict(file_text)
    return headers


def get_log_info(login_file=Path("loginfo.txt")):
    file_text = get_file_text(login_file)
    log_info = clean_to_dict(file_text)
    return log_info


def scrape(url, session, headers = {}):
    info = session.get(url, headers=headers)
    soup = BeautifulSoup(info.content, "html.parser")
    incidents = [incident.text for incident in soup.findAll("p")]
    date = soup.find("time").text
    pdcity = soup.find("h1").text.split()[0]
    return incidents, date, pdcity


def main(url, header_file=Path("headersinfo.txt"), login_file=Path("loginfo.txt")):
    headers = get_headers(header_file)
    log_info = get_log_info(login_file)
    with requests.Session() as session:
        login(
            "https://www.rep-am.com/login", session, headers = headers, log_info = log_info)
        incidents = scrape(url, session)
        with ChangeDirManager("../data"):
            with open(new_file:=f"dirty_{url[-4:-1]}.json", "w") as f:
                json.dump(incidents, f)
        return new_file


if __name__ == "__main__":
    # headers = {}
    # headers = clean(get_file_text("headersinfo.txt"), "\n")
    # log_info = {}
    # log_info = clean(get_file_text("loginfo.txt"), "\n")
    try:
        url = sys.argv[1]
    except IndexError:
        url = input("What url to scrape?")
    with requests.Session() as session:
        main(url=url)
        # login(
        #     "https://www.rep-am.com/login", session, headers = headers, log_info = log_info)
        # # url = "https://www.rep-am.com/local/records/police/2019/11/22/torrington-police-blotter-65/"
        # try:
        #     info = session.get(url)
        # except requests.RequestException as rex:
        #     print(str(rex))
        # else:
        #     soup = BeautifulSoup(info.content, "html.parser")
        #     with open("test.txt", "w") as f:
        #         f.write(str(soup))
        #     incidents = []
        #     for incident in soup.findAll("p"):
        #         incidents.append(incident.text)
        #     with open(f"dirty_{url[-4:-1]}.txt", "w") as f:
        #         f.write(str(incidents))