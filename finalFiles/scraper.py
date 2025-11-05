import bs4
import datetime
from customFunctions import safeGet
import re
import classes


#So that 12 months of fixtures can be fetched from the date of request
def getNextTwelveMonths():
    currentDate = datetime.datetime.now()
    months = []
    year = currentDate.year
    month = currentDate.month

    for monthNumber in range(12):
        monthString = str(month)
        if len(monthString) == 1:
            monthString = "0" + monthString
        yearMonth = f"{year}-{monthString}"
        months.append(yearMonth)
        month += 1
        if month > 12:
            month = 1
            year += 1

    return months #results in [yyyy-mm, ...]


#To get the actual numerical date of the month from the string fetched because it is originally in a form like "Saturday 12th December"
def getDate(monthYear, restOfDate):
    dayNumber = re.search(r"\d{1,2}", restOfDate).group()
    if len(dayNumber) == 1:
        dayNumber = "0" + dayNumber
    year, month = monthYear.split("-")
    date = f"{dayNumber}-{month}-{year}"
    return date


def getPageFixtures(url, monthYear, tierName, fixtures):
    response = safeGet(url)
    soup = bs4.BeautifulSoup(response.text, "html.parser")

    #On the webpage, the fixtures are below each date, so fetch the date first and find all fixtures until the next date, so that these fixtures can be stored under the stored date
    for tag in soup.find_all(["h2", "span"]):
        if tag.name == "h2": #This is where the date can be found
            text = tag.get_text(strip=True)
            currentDateText = text
            if currentDateText != "Best of the BBC": #Some headings are this instead of the date
                currentDate = getDate(monthYear, currentDateText)
                #Creates a list to hold fixtures of the current date. If already made by another league, this prevents it being overwritten
                try:
                    test = fixtures[currentDate]
                except:
                    fixtures[currentDate] = []
            else:
                pass

        elif tag.name == "span" and "versus" in tag.get_text(): #Where fixtures are stored
            if currentDate != "Best of the BBC":
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
                    "league" : tierName,
                    "home": home,
                    "away": away.strip(),
                    "time": time
                })

    return fixtures


def main():
    fixtures = {}
    tiers = {
        "Premier League": "premier-league",
        "Championship": "championship",
        "League One": "league-one",
        "League Two": "league-two",
    }

    dateAdditions = getNextTwelveMonths()

    #Results in a dictionary of lists containing dictionaries in the format : {Date: [{"league" : "A", "home" : "B", "away" : "C", "time" : "D"}]}
    for tierName in tiers.keys():
        tierID = tiers[tierName]
        for dateAddition in dateAdditions:
            url = f"https://www.bbc.co.uk/sport/football/{tierID}/scores-fixtures/{dateAddition}"
            fixtures = getPageFixtures(url, dateAddition, tierName, fixtures)

    #Stores everything into classes so that methods may be applied
    dateObjectList = []
    for dateString in fixtures.keys():
        listOfFixtureObjects = []
        for fixtureDictionary in fixtures[dateString]:
            league = fixtureDictionary["league"]
            home = fixtureDictionary["home"]
            away = fixtureDictionary["away"]
            time = fixtureDictionary["time"]
            fixtureObject = classes.Fixture(league, home, away, time)
            listOfFixtureObjects.append(fixtureObject)
        dateObject = classes.Date(dateString, listOfFixtureObjects)
        dateObjectList.append(dateObject)
    AllDatesObject = classes.AllDates(dateObjectList)

    for dateObject in AllDatesObject.dates:
        print(dateObject.date)
        for fixture in dateObject.fixtures:
            print(fixture.league, fixture.home, fixture.away, fixture.time)

if __name__ == '__main__':
    main()