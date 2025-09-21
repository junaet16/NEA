import sqlite3
import requests
import math
import collections
import heapq
from classes import *


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


def fetchStations(TfL_API_KEY, lineIDs):
    stationDictionary = {}
    params = {
        "app_key": TfL_API_KEY,
    }
    for line in lineIDs:
            url = f"https://api.tfl.gov.uk/Line/{line}/Route/Sequence/inbound"
            response = requests.get(url, params=params)
            data = response.json()
            stations = data["stations"]
            for station in stations:
                if station["id"] not in stationDictionary:
                    stationDictionary[station["id"]] = Station(station, lineIDs)
    return stationDictionary


def fetch_lines(stationDictionary, TfL_API_KEY, lineIDs):
    linesDictionary = {}
    weirdStations = {} #Some stations are returned strangely by the API so this is just to handle it
    params = {
        "app_key": TfL_API_KEY,
    }
    for line in lineIDs:
        url = f"https://api.tfl.gov.uk/Line/{line}/Route/Sequence/inbound"
        response = requests.get(url, params=params)
        data = response.json()
        branches = data["orderedLineRoutes"]
        listOflistsOfNAPTAN = []
        for branchAllData in branches: #branchAllData contains a list of NaPTAN IDs, but also other data which I don't need
            branch = branchAllData["naptanIds"]
            for i, id in enumerate(branch):
                if id not in stationDictionary: #All possible unique stations already exist in stationDictionary, but some stations have other IDs for different modes, which maeans they need to be filtered out so that there is only one ID per station
                    if id not in weirdStations: #Store of all the stations that have different IDs
                        newURL = f"https://api.tfl.gov.uk/StopPoint/{id}"
                        newResponse = requests.get(newURL, params=params)
                        newData = newResponse.json()
                        newId = newData["hubNaptanCode"] #Collects the ID that represents the entire station and not just that mode/line
                        weirdStations[id] = newId
                    id = weirdStations[id]
                    branch[i] = id
            listOflistsOfNAPTAN.append(branch)
        linesDictionary[line] = listOflistsOfNAPTAN
    return linesDictionary


def fetchTfLData(databaseFile, TfL_API_KEY):
    connection = sqlite3.connect(databaseFile)
    cursor = connection.cursor()

    #Creates a list of LineIDs
    linesCursorObject = cursor.execute("SELECT LineID FROM Lines")
    lineIDs = []
    for lineTuple in linesCursorObject:
        lineIDs.append(lineTuple[0])

    stationDictionary = fetchStations(TfL_API_KEY, lineIDs)
    linesDictionary = fetch_lines(stationDictionary, TfL_API_KEY, lineIDs)

    connection.close()
    return stationDictionary, linesDictionary


def getStationLineRelationships(databseFile):
    connection = sqlite3.connect(databseFile)
    cursor = connection.cursor()
    megaList = []

    rows = cursor.execute("SELECT StationA, LineID from Connections").fetchall()
    for row in rows:
        StationA = row[0]
        LineID = row[1]
        cursor.execute("""
            INSERT OR IGNORE INTO StationLineRelationships (NaPTAN, LineID) 
            VALUES (?, ?)
            """, (StationA, LineID))

    connection.commit()
    connection.close()


def SaveTfLData(databaseFile, TfL_API_KEY):
    stationDictionary, linesDictionary = fetchTfLData(databaseFile, TfL_API_KEY)
    connection = sqlite3.connect(databaseFile)
    cursor = connection.cursor()

    for station in stationDictionary.values():
        NaPTAN = station.NaPTAN
        StationName = station.StationName
        Latitude = station.Latitude
        Longitude = station.Longitude
        TravelZone = station.TravelZone
        cursor.execute("""
            INSERT INTO Stations (NaPTAN, StationName, Latitude, Longitude, TravelZone) 
            VALUES (?, ?, ?, ?, ?)
            """, (NaPTAN, StationName, Latitude, Longitude, TravelZone))

    for line in linesDictionary.keys():
        LineID = line
        branches = linesDictionary[line]
        for branch in branches:
            for i in range(len(branch) - 1):
                try:
                    StationA = branch[i]
                    StationB = branch[i + 1]

                    BaseTravelTime = 3 #Calculate Base Travel Time Here Later

                    #So that reverse is possible
                    cursor.execute("""
                        INSERT INTO Connections (StationA, StationB, LineID, BaseTravelTime)
                        VALUES (?, ?, ?, ?)
                        """, (StationA, StationB, LineID, BaseTravelTime))
                    cursor.execute("""
                        INSERT INTO Connections (StationA, StationB, LineID, BaseTravelTime)
                        VALUES (?, ?, ?, ?)
                        """, (StationB, StationA, LineID, BaseTravelTime))
                except:
                    pass

    getStationLineRelationships(databaseFile)

    connection.commit()
    connection.close()


def MakeGraph(databaseFile):
    connection = sqlite3.connect(databaseFile)
    cursor = connection.cursor()
    crowdingNumber = 0
    crowdingScore = 0
    listOfNeighbourStations = {} #Just to gather unique [StationA, StationB, LineID]
    listOfNeighbourData = {} #Actual node to be used
    rows = cursor.execute("SELECT StationA, StationB, LineID, BaseTravelTime FROM connections").fetchall()

    for StationA, StationB, LineID, BaseTravelTime in rows: #For every unique connection (direction matters)
        totalTime = BaseTravelTime
        if StationA not in listOfNeighbourStations:
            listOfNeighbourStations[StationA] = []
            listOfNeighbourData[StationA] = []
        if [StationB, BaseTravelTime, LineID] not in listOfNeighbourStations[StationA]:
            listOfNeighbourStations[StationA].append([StationB, BaseTravelTime, LineID])
            listOfNeighbourData[StationA].append([StationB, BaseTravelTime, LineID, crowdingNumber, crowdingScore, totalTime])

    connection.close()
    return listOfNeighbourData


def Dijkstra(mode, listOfNeighbourData, start, goal):
    pass #Figure this out


def main():
    TfL_API_KEY = "0ff5a2076cd640cb957e63d6947efc61"
    databaseFile = "test.db" #Could change name later to something more appropriate
    #SaveTfLData(databaseFile, TfL_API_KEY) Only need to be run once


if __name__ == "__main__":
    main()