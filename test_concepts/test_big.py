import sqlite3
import requests
import math
import collections
import heapq
from classes import *


#Basically done
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


#Need to edit line data
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


#Need to add functions for venues and stuff
def insertDefault(databaseFile):
    #createDatabase(databaseFile) #Only need to run once
    #createLines(databaseFile) #Only need to run once
    pass


#Basically done
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
                    stationDictionary[station["id"]] = Station(station)
    return stationDictionary


#Basically done
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


#Need to add stuff that will prevent it crashing when can't get data
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


#Basically done
def getStationLineRelationships(databseFile):
    connection = sqlite3.connect(databseFile)
    cursor = connection.cursor()

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


#Basically done
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


#Basically done
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
        if [StationB, BaseTravelTime, LineID] not in listOfNeighbourStations[StationA]:
            listOfNeighbourStations[StationA].append([StationB, BaseTravelTime, LineID])

    connection.close()
    return listOfNeighbourStations


def Dijkstra(graph, startStation, goalStation, CHANGING_TIME, penalty=True):
    distances = collections.defaultdict(lambda: math.inf) #Best known time to each station
    cameFrom = {} #To reconstruct path later
    visited = set() #Stores visited stations

    # Start at the given station, with no line yet chosen
    startState = (startStation, None)
    distances[startState] = 0

    frontier = [(0, startState)] #The first item is always the cheapest station to go to next
    goalState = None #Store the final when we reach the goal


    while frontier: #This condition means it runs until all the paths have been explored - till the last one
        currentCost, (currentStation, currentLine) = heapq.heappop(frontier) #Deletes the next route at the top so that the next one to be explored can be at the top

        # Skip if already fully explored this (station, line) - If at the top of the heap, then it means that it is the shortest ever path to the station
        if (currentStation, currentLine) in visited:
            continue
        visited.add((currentStation, currentLine))

        # Stop if reached the goal station
        if currentStation == goalStation:
            goalState = (currentStation, currentLine)
            break

        # Explore all neighbours of this station
        for nextStation, baseTravelTime, nextLine in graph[currentStation]:
            travelTime = baseTravelTime

            if penalty: #Can be turned off if needed
                if currentLine is not None and currentLine != nextLine:
                    travelTime += CHANGING_TIME

            # New total time to reach the neighbour
            newCost = currentCost + travelTime
            neighbourState = (nextStation, nextLine)

            # Only update if we found a faster way
            if newCost < distances[neighbourState]:
                distances[neighbourState] = newCost
                cameFrom[neighbourState] = (currentStation, currentLine, nextLine)
                heapq.heappush(frontier, (newCost, neighbourState))

    # Start from the goal and trace back to the start
    pathSteps = []
    currentState = goalState

    while currentState != startState:
        prevStation, prevLine, lineUsed = cameFrom[currentState]
        currStation, currLine = currentState
        pathSteps.append((prevStation, currStation, lineUsed, distances[(currStation, currLine)]))
        currentState = (prevStation, prevLine)


    pathSteps.reverse()
    return pathSteps


def main():
    TfL_API_KEY = "0ff5a2076cd640cb957e63d6947efc61"
    databaseFile = "test.db" #Could change name later to something more appropriate
    #SaveTfLData(databaseFile, TfL_API_KEY) Only need to be run once

if __name__ == "__main__":
    main()