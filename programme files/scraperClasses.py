import sqlite3



#GLOBAL PARAMETERS
#Duration of a match including breaks
DURATION = 120 # Minutes



# Fixture object acts as a container for scraped fixture data for me
class Fixture():
    def __init__(self, league, home, away, time):
        self.league = league # League the fixture belongs to (e.g. Premier League)
        self.home = home # Home team
        self.away = away # Away team
        self.time = time # Kick-off time (or TBC)



#Date object contains the date and a list of fixture objects
#Date object's findRelevantFixtures method deletes all fixtures not in London
class Date():
    def __init__(self, date, fixtures):
        self.date = date # Date in dd-mm-yyyy format
        self.fixtures = fixtures # List of Fixture objects on this date


    # Removes all fixtures whose home team is not a London club
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

        # Replace fixtures list with only relevant fixtures
        self.fixtures = relevantFixtures



#Contains a list of date objects
class AllDates():
    def __init__(self, dates):
        self.dates = dates # List of Date objects


    # Filters out dates that do not contain any London fixtures and the fixtures on that date that are not relevant
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
            # Filter fixtures within the date
            dateObject.findRelevantFixtures(londonClubs) #Filters out all non-relevant

            # Only keep dates that still contain at least one fixture
            if len(dateObject.fixtures) != 0:
                relevantDates.append(dateObject) #This means at least one event on this date is in London
        self.dates = relevantDates

        connection.close()


    # Stores all remaining fixtures into the Events table
    def storeInDatabase(self, databaseFile):
        connection = sqlite3.connect(databaseFile)
        cursor = connection.cursor()

        # Convert date format from dd-mm-yyyy to dd/mm/yyyy
        for dateObject in self.dates:
            Date = dateObject.date
            day, month, year = Date.split("-")
            Date = f"{day}/{month}/{year}"
            for fixture in dateObject.fixtures:
                HomeTeam = fixture.home
                AwayTeam = fixture.away
                Time = fixture.time
                Name = fixture.league

                # Fetch the venue associated with the home team
                cursor.execute("""
                SELECT VenueName
                FROM Teams
                WHERE TeamName = ?
                """, (HomeTeam,))
                VenueName = cursor.fetchall()[0][0]

                # Store the event in the Events table
                # Duration is fixed as an assumption
                cursor.execute("""
                INSERT OR REPLACE INTO Events (VenueName, Date, Time, HomeTeam, AwayTeam, EventName, Duration)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (VenueName, Date, Time, HomeTeam, AwayTeam, Name, DURATION),)

                connection.commit()

        connection.close()