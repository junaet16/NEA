import sqlite3
import json
import getTfLData
import storeStadiumData
import scraper


#Creates the database
def createDatabase(databaseFile):
    connection = sqlite3.connect(databaseFile)
    cursor = connection.cursor()

    cursor.executescript("""

        CREATE TABLE IF NOT EXISTS Stations (
            NaPTAN TEXT PRIMARY KEY,
            StationName TEXT,
            Latitude REAL,
            Longitude REAL
        );

        CREATE TABLE IF NOT EXISTS Lines (
            LineID TEXT PRIMARY KEY,
            LineName TEXT,
            AverageSpeed TEXT                  
        );

        CREATE TABLE IF NOT EXISTS StationLineRelationships (
            NaPTAN TEXT,
            LineID TEXT,
            PRIMARY KEY (NaPTAN, LineID),
            FOREIGN KEY (NaPTAN) REFERENCES Stations(NaPTAN),
            FOREIGN KEY (LineID) REFERENCES Lines(LineID)
        );

        CREATE TABLE IF NOT EXISTS Connections (
            StationA TEXT,
            StationB TEXT,
            LineID TEXT,
            BaseTravelTime REAL,
            PRIMARY KEY (StationA, StationB, LineID),
            FOREIGN KEY (StationA) REFERENCES Stations(NaPTAN),
            FOREIGN KEY (StationB) REFERENCES Stations(NaPTAN),
            FOREIGN KEY (LineID) REFERENCES Lines(LineID)
        );

        CREATE TABLE IF NOT EXISTS Venues (
            VenueName TEXT PRIMARY KEY,
            Capacity INTEGER,
            Latitude REAL,
            Longitude REAL
        );

        CREATE TABLE IF NOT EXISTS VenueStationRelationships (
            VenueName TEXT,
            NaPTAN TEXT,
            Distance REAL,
            PRIMARY KEY (VenueName, NaPTAN),
            FOREIGN KEY (VenueName) REFERENCES Venues(VenueName),
            FOREIGN KEY (NaPTAN) REFERENCES Stations(NaPTAN)
        );

        CREATE TABLE IF NOT EXISTS Events (
            VenueName TEXT,
            Date TEXT,
            Time TEXT,
            HomeTeam TEXT,
            AwayTeam TEXT,
            EventName TEXT,
            Duration INTEGER,
            PRIMARY KEY (VenueName, Date),
            FOREIGN KEY (VenueName) REFERENCES Venues(VenueName),
            FOREIGN KEY (HomeTeam) REFERENCES Teams(TeamName)
        );

        CREATE TABLE IF NOT EXISTS Users (
            Username TEXT PRIMARY KEY,
            PasswordHash TEXT,
            Salt,
            CHANGING_TIME REAL,
            MAX_TIME_WINDOW REAL,
            rawArrivalPeakOffset REAL,
            rawDeparturePeakOffset REAL,
            ATTENDANCE REAL,
            TRAIN_PROPORTION REAL,
            SIGMA_FACTOR REAL,
            MINIMUM_PEOPLE REAL,
            PERSON_DELAY REAL,
            PROPAGATION_FACTOR REAL,
            WALKING_TIME REAL,
            WALKING_SPEED REAL,
            NORMAL REAL,
            SLIGHTLY REAL,
            BUSY REAL
        );

        CREATE TABLE IF NOT EXISTS Teams (
            TeamName TEXT PRIMARY KEY,
            VenueName TEXT,
            FOREIGN KEY (VenueName) REFERENCES Venues(VenueName)
        );

    """)

    connection.commit()
    connection.close()


#Puts all the data regarding each line into the database
#Line speeds are in kmh^-1
#Source:
#https://tfl.gov.uk/corporate/transparency/freedom-of-information/foi-request-detail?referenceId=FOI-0228-1819 - Underground & Overground
#https://www.independent.co.uk/travel/news-and-advice/london-dlr-trains-speed-restrictions-b2613480.html - DLR
#https://tfl.gov.uk/corporate/transparency/freedom-of-information/foi-request-detail?referenceId=FOI-1394-2223 - Elizabeth Line
def createLines(databaseFile, jsonFile):
    connection = sqlite3.connect(databaseFile)
    cursor = connection.cursor()

    with open(jsonFile, "r") as file:
        LineInfo = json.load(file)

    for lineID, (LineName, AverageSpeed) in LineInfo.items():
        cursor.execute("""
            INSERT OR REPLACE INTO Lines (LineID, LineName, AverageSpeed)
            VALUES (?, ?, ?)
        """, (lineID, LineName, AverageSpeed))

    connection.commit()
    connection.close()


def getWalking(file):
    with open(file, "r") as jsonFile:
        data = json.load(jsonFile)
    walkingSpeed = data.get("WALKING_SPEED")
    walkingTime = data.get("WALKING_TIME")
    return walkingSpeed, walkingTime


def main(databaseFile, LinesjsonFile, TfL_API_KEY, OPENCAGE_API_KEY, londonjsonFile, leaguesjsonFile, defaultParametersFile):
    walkingSpeed, walkingTime = getWalking(defaultParametersFile)

    createDatabase(databaseFile)
    print("Created Database")
    createLines(databaseFile, LinesjsonFile)
    print("Created Lines")
    getTfLData.main(TfL_API_KEY, databaseFile)
    print("Got TFL Data")
    storeStadiumData.main(OPENCAGE_API_KEY, londonjsonFile, databaseFile, walkingTime, walkingSpeed)
    print("Stored Stadium Data")
    scraper.main(databaseFile, leaguesjsonFile)
    print("Done Scraping")


if __name__ == '__main__':
    main("final.db", "lines.json", "0ff5a2076cd640cb957e63d6947efc61", "eb0e2c9b71cc45f7aafe0ae4ecc44cc2", "londonClubs.json", "leagues.json", "defaultParameters.json")
