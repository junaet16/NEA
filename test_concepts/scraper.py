import requests
import bs4
from bs4 import BeautifulSoup
from datetime import datetime

def get_elf_fixtures(url):
    url = url + "/2025-12"
    response = requests.get(url)
    soup = bs4.BeautifulSoup(response.text, "html.parser")
    fixtures = []

    #I'll do a thing where I automatically get all the dates but ima try just one month for now


def main():
    urlsPart = {"Premier League": "premier-league"}
    for urlPartKey in urlsPart.keys():
        urlPart = urlsPart[urlPartKey]
        url = f"https://www.bbc.co.uk/sport/football/{urlPart}/scores-fixtures"
        get_elf_fixtures(url)


if __name__ == '__main__':
    main()