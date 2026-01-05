import sqlite3

class Fixture():
    def __init__(self, league, home, away, time):
        self.league = league
        self.home = home
        self.away = away
        self.time = time


#Date object contains the date and a list of fixture objects
#Date object's findRelevantFixtures method deletes all fixtures not in London
class Date():
    def __init__(self, date, fixtures):
        self.date = date
        self.fixtures = fixtures

    def findRelevantFixtures(self, londonClubs):
        relevantFixtures = []
        for fixture in self.fixtures:
            home = fixture.home
            London = False
            #Check if home is in London
            if home in londonClubs:
                London = True
            if London:
                relevantFixtures.append(fixture)
        self.fixtures = relevantFixtures


#Contains a list of date objects
class AllDates():
    def __init__(self, dates):
        self.dates = dates

    def findRelevantDates(self, databaseFile):
        connection = sqlite3.connect(databaseFile)
        cursor = connection.cursor()
        londonClubs = []

        cursor.execute("""
            SELECT TeamName
            FROM Teams
        """)
        rows = cursor.fetchall()
        for clubTuple in rows:
            londonClubs.append(clubTuple[0])

        relevantDates = []
        for dateObject in self.dates:
            dateObject.findRelevantFixtures(londonClubs) #Filters out all non-relevant
            if len(dateObject.fixtures) != 0:
                relevantDates.append(dateObject) #This means at least one event on this date is in London
        self.dates = relevantDates

        connection.close()

    def storeInDatabase(self, databaseFile):
        connection = sqlite3.connect(databaseFile)
        cursor = connection.cursor()

        for dateObject in self.dates:
            Date = dateObject.date
            day, month, year = Date.split("-")
            Date = f"{day}/{month}/{year}"
            for fixture in dateObject.fixtures:
                HomeTeam = fixture.home
                AwayTeam = fixture.away
                Time = fixture.time
                Name = fixture.league

                cursor.execute("""
                SELECT VenueName
                FROM Teams
                WHERE TeamName = ?
                """, (HomeTeam,))
                VenueName = cursor.fetchall()[0][0]

                cursor.execute("""
                INSERT OR REPLACE INTO Events (VenueName, Date, Time, HomeTeam, AwayTeam, EventName, Duration)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (VenueName, Date, Time, HomeTeam, AwayTeam, Name, 120),)

                connection.commit()

        connection.close()
