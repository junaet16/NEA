import sqlite3
import json


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
            FOREIGN KEY (VenueName) REFERENCES Venues(VenueName)
        );

        CREATE TABLE IF NOT EXISTS Users (
            UserID INTEGER PRIMARY KEY AUTOINCREMENT,
            Username TEXT,
            PasswordHash TEXT,
            Email TEXT
        );

        CREATE TABLE IF NOT EXISTS Teams (
            TeamName TEXT PRIMARY KEY,
            VenueName TEXT
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


def main(databaseFile, jsonFile):
    createDatabase(databaseFile)
    createLines(databaseFile, jsonFile)


if __name__ == '__main__':
    main("final.db", "lines.json")