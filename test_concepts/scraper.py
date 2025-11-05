import requests
import bs4
from datetime import datetime

def get_elf_fixtures(url):
    url = url + "/2025-12"
    response = requests.get(url)
    soup = bs4.BeautifulSoup(response.text, "html.parser")
    fixtures = {}
    for tag in soup.find_all(["h2", "span"]):
        if tag.name == "h2":
            text = tag.get_text(strip=True)
            currentDate = text
            fixtures[currentDate] = []

        elif tag.name == "span" and "versus" in tag.get_text():
            text = tag.get_text(strip=True)
            parts = text.split("versus")
            home = parts[0].strip()
            away_time = parts[1].strip()

            # Extract time if present
            if "kick off" in away_time:
                away, time = away_time.split(" kick off ")
                time = time.strip()
            else:
                away, time = away_time, "TBC"

            fixtures[currentDate].append({
                "home": home,
                "away": away.strip(),
                "time": time
            })

    for date in fixtures.keys():
        print(date)
        print(fixtures[date])

    #I'll do a thing where I automatically get all the dates but ima try just one month for now


def main():
    urlsPart = {"Premier League": "premier-league"}
    for urlPartKey in urlsPart.keys():
        urlPart = urlsPart[urlPartKey]
        url = f"https://www.bbc.co.uk/sport/football/{urlPart}/scores-fixtures"
        get_elf_fixtures(url)


if __name__ == '__main__':
    main()