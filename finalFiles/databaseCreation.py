import sqlite3
import json
import getTfLData
import storeStadiumData
import scraper


# Creates the SQLite database and all required tables
# If tables already exist, they will not be recreated
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
            Salt TEXT,
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


#Puts all the data for me regarding each line into the database
#Line speeds are in kmh^-1
def createLines(databaseFile, jsonFile):
    connection = sqlite3.connect(databaseFile)
    cursor = connection.cursor()

    # Load line information from JSON file
    with open(jsonFile, "r") as file:
        LineInfo = json.load(file)

    # Insert or update each line in the Lines table
    for lineID, (LineName, AverageSpeed) in LineInfo.items():
        cursor.execute("""
            INSERT OR REPLACE INTO Lines (LineID, LineName, AverageSpeed)
            VALUES (?, ?, ?)
        """, (lineID, LineName, AverageSpeed))

    connection.commit()
    connection.close()


# Reads default walking parameters from a JSON configuration file
def getWalking(file):
    with open(file, "r") as jsonFile:
        data = json.load(jsonFile)

    # Extract walking speed and walking time parameters
    walkingSpeed = data.get("WALKING_SPEED")
    walkingTime = data.get("WALKING_TIME")
    return walkingSpeed, walkingTime


#Main sequence of steps for building and populating the database
def main(databaseFile, LinesjsonFile, TfL_API_KEY, OPENCAGE_API_KEY, londonjsonFile, leaguesjsonFile, defaultParametersFile):

    # Load walking parameters used for venue station relationships
    walkingSpeed, walkingTime = getWalking(defaultParametersFile)

    # Create database schema
    createDatabase(databaseFile)
    print("Created Database")

    # Populate Lines table
    createLines(databaseFile, LinesjsonFile)
    print("Created Lines")

    # Fetch and store TfL transport data for me
    tflDone = getTfLData.main(TfL_API_KEY, databaseFile)
    if type(tflDone) == int: #When an error has occurred a status code will be returned
        return tflDone
        pass
    print("Got TFL Data")

    # Geocode stadiums and link them to stations with default walking parameters
    geocodingMessage = storeStadiumData.main(OPENCAGE_API_KEY, londonjsonFile, databaseFile, walkingTime, walkingSpeed)
    if type(geocodingMessage) != bool:
        return geocodingMessage
    print("Stored Stadium Data")

    #Scrape event data for me
    scraperMessage = scraper.main(databaseFile, leaguesjsonFile)
    if type(scraperMessage) is int:
        return scraperMessage
    print("Done Scraping")

    return "success"


# Run main (remnant of testing)
if __name__ == '__main__':
    message = main("final.db", "lines.json", "0ff5a2076cd640cb957e63d6947efc61", "eb0e2c9b71cc45f7aafe0ae4ecc44cc2", "londonClubs.json", "leagues.json", "defaultParameters.json")
    print(message)