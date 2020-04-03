"""Provide functions necessary for scraping rep-am.com"""
import requests

from bs4 import BeautifulSoup


def login(url, session, headers=None, log_info=None):
    """Log into url using POST.

    Logs into a site on the web given by url, using provided login information
    and headers through POST method. The session is maintained.
    """
    if headers is None:
        headers = {}
    if log_info is None:
        log_info = {}
    try:
        response = session.post(url, data=log_info, headers=headers)
    except requests.RequestException as rex:
        print(str(rex))
    else:
        return response


def scrape(url, session, headers=None):
    """Scrape a given url for content

    Scrape a given url (preferably from rep-am.com) for date posted, police
    department from whom the records are sourced, and any records.
    """
    if headers is None:
        headers = {}
    info = session.get(url, headers=headers)
    soup = BeautifulSoup(info.content, "html.parser")
    incidents = [incident.text for incident in soup.findAll("p")]
    date = soup.find("time").text
    pdcity = soup.find("h1").text.split()[0]
    return incidents, date, pdcity
