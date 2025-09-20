import sqlite3
import requests
import math
import collections
import heapq


def createDatabase(databaseFile):
    connection = sqlite3.connect(databaseFile)
    cursor = connection.cursor()

    cursor.executescript("""
    
        CREATE TABLE IF NOT EXISTS Stations (
            NaPTAN TEXT PRIMARY KEY,
            StationName TEXT,
            Latitude REAL,
            Longitude REAL,
            TravelZone TEXT
        );

        CREATE TABLE IF NOT EXISTS Lines (
            LineID TEXT PRIMARY KEY,
            LineName TEXT,
            LineColour REAL,  
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
            PRIMARY KEY (VenueName, Date),
            FOREIGN KEY (VenueName) REFERENCES Venues(VenueName)
        );
        
        CREATE TABLE IF NOT EXISTS Users (
            UserID INTEGER PRIMARY KEY AUTOINCREMENT,
            Username TEXT,
            PasswordHash TEXT,
            Email TEXT
        );
        
        CREATE TABLE IF NOT EXISTS StandardRoutes (
            RouteID INTEGER PRIMARY KEY AUTOINCREMENT,
            UserID INTEGER,
            StartStationID TEXT,
            EndStationID TEXT,
            FOREIGN KEY (UserID) REFERENCES Users(UserID),
            FOREIGN KEY (StartStationID) REFERENCES Stations(NaPTAN),
            FOREIGN KEY (EndStationID) REFERENCES Stations(NaPTAN)
        );
        
        CREATE TABLE IF NOT EXISTS Teams (
            TeamName TEXT PRIMARY KEY,
            VenueName TEXT
        );

    """)


    connection.commit()
    connection.close()


def createLines(databaseFile):
    #List Format: [Name, Colour, AverageSpeed]
    #For now all the colours will be "DefaultColour" and the AverageSpeeds will be 3
    connection = sqlite3.connect(databaseFile)
    cursor = connection.cursor()
    LineInfo = {
        "bakerloo":["Bakerloo Line", "DefaultColour", 3],
        "central":["Central Line", "DefaultColour", 3],
        "circle":["Circle Line", "DefaultColour", 3],
        "district":["District Line", "DefaultColour", 3],
        "hammersmith-city":["Hammersmith and City Line", "DefaultColour", 3],
        "jubilee":["Jubilee Line", "DefaultColour", 3],
        "metropolitan":["Metropolitan Line", "DefaultColour", 3],
        "northern":["Northern Line", "DefaultColour", 3],
        "piccadilly":["Piccadilly Line", "DefaultColour", 3],
        "victoria":["Victoria Line", "DefaultColour", 3],
        "waterloo-city":["Waterloo and City Line", "DefaultColour", 3],
        "dlr":["DLR", "DefaultColour", 3],
        "elizabeth":["Elizabth Line", "DefaultColour", 3],
        "liberty":["Liberty Line", "DefaultColour", 3],
        "lioness":["Lioness Line", "DefaultColour", 3],
        "mildmay":["Mildmay Line", "DefaultColour", 3],
        "windrush":["Windrush Line", "DefaultColour", 3],
        "weaver":["Weaver Line", "DefaultColour", 3],
        "suffragette":["Suffragette Line", "DefaultColour", 3]
    }

    for lineID in LineInfo.keys():
        LineName = LineInfo[lineID][0]
        LineColour = LineInfo[lineID][1]
        AverageSpeed = LineInfo[lineID][2]
        cursor.execute("""
            INSERT INTO Lines (LineID, LineName, LineColour, AverageSpeed) 
            VALUES (?, ?, ?, ?)
        """, (lineID, LineName, LineColour, AverageSpeed))

    connection.commit()
    connection.close()


def insertDefault(databaseFile):
    #createDatabase(databaseFile) #Only need to run once
    #createLines(databaseFile) #Only need to run once
    pass


def fetchTfLData(databaseFile):
    connection = sqlite3.connect(databaseFile)
    cursor = connection.cursor()
    linesCursorObject = cursor.execute("SELECT LineID FROM Lines")
    lineIDs = []
    for lineTuple in linesCursorObject:
        lineIDs.append(lineTuple[0])
    print(lineIDs)


def main():
    databaseFile = "test.db" #Could change name later to something more appropriate
    insertDefault(databaseFile)
    fetchTfLData(databaseFile)


if __name__ == "__main__":
    main()