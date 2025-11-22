import sqlite3
import classes
from customFunctions import safeGet
from geopy.distance import geodesic


# Creates a dictionary with the format - {NaPTAN : Station object}
def fetchStations(TfL_API_KEY, lineIDs):
    stationDictionary = {}
    params = {
        "app_key": TfL_API_KEY,
    }

    for line in lineIDs:
        url = f"https://api.tfl.gov.uk/Line/{line}/Route/Sequence/inbound"
        response = safeGet(url, params=params)
        data = response.json()
        stations = data["stations"]
        for station in stations:
            if station["id"] not in stationDictionary:  # So every entry is unique
                NaPTAN = station['id']
                StationName = station['name']
                Latitude = station['lat']
                Longitude = station['lon']
                stationDictionary[station["id"]] = classes.CreationStation(NaPTAN, StationName, Latitude, Longitude)
    return stationDictionary


# Uses a list of LineIDs and a list of Station objects to create a dictionary in the form {LineID : [[Branch1], [Branch2], ..., [Branchn]]
def fetch_lines(stationDictionary, TfL_API_KEY, lineIDs):
    linesDictionary = {}  # Final dictionary that will be returned
    weirdStations = {}  # Some stations are returned strangely by the API so this is just to handle it - some stations have different IDs for different branches and therefore don't align with their IDs in the database, so this dictionary will be in the form - {notCorrectID : correctID}
    params = {
        "app_key": TfL_API_KEY,
    }

    for line in lineIDs:
        url = f"https://api.tfl.gov.uk/Line/{line}/Route/Sequence/inbound"
        response = safeGet(url, params=params)
        data = response.json()
        branches = data["orderedLineRoutes"]
        listOflistsOfNAPTAN = []
        for branchAllData in branches:  # branchAllData contains a list of NaPTAN IDs, but also other data which I don't need
            branch = branchAllData["naptanIds"]  # List of all stations (NaPTAN IDs) of the branch
            for i, id in enumerate(branch):
                if id not in stationDictionary:  # All possible unique stations already exist in stationDictionary, but some stations have other IDs for different modes, which means they need to be filtered out so that there is only one ID per station
                    if id not in weirdStations:  # Store of all the stations that have different IDs
                        newURL = f"https://api.tfl.gov.uk/StopPoint/{id}"  # Fetches all data regarding that particular station
                        newResponse = safeGet(newURL, params=params)
                        newData = newResponse.json()
                        newId = newData["hubNaptanCode"]  # Collects the ID that represents the entire station and not just that mode/line
                        weirdStations[id] = newId
                    id = weirdStations[id]
                    branch[i] = id  # Changes the ID of the station in the branch to the correct ID
            listOflistsOfNAPTAN.append(branch)
        linesDictionary[line] = listOflistsOfNAPTAN
    return linesDictionary


def fetchTfLData(databaseFile, TfL_API_KEY):
    connection = sqlite3.connect(databaseFile)
    cursor = connection.cursor()

    # Creates a list of LineIDs
    linesCursorObject = cursor.execute("SELECT LineID FROM Lines")
    lineIDs = []
    for lineTuple in linesCursorObject:  # Because the SQL returns the data in the form (LineID,)
        lineIDs.append(lineTuple[0])

    stationDictionary = fetchStations(TfL_API_KEY, lineIDs)
    linesDictionary = fetch_lines(stationDictionary, TfL_API_KEY, lineIDs)

    connection.close()
    return stationDictionary, linesDictionary


# Puts every possible Station, Line pair and puts it into the database
def getStationLineRelationships(databseFile):
    connection = sqlite3.connect(databseFile)
    cursor = connection.cursor()

    rows = cursor.execute("SELECT StationA, LineID from Connections").fetchall()
    for row in rows:
        StationA = row[0]
        LineID = row[1]

        # Ignore as well because station might have more than 1 connection to another station via the same line
        cursor.execute("""
            INSERT OR REPLACE INTO StationLineRelationships (NaPTAN, LineID) 
            VALUES (?, ?)
            """, (StationA, LineID))

    connection.commit()
    connection.close()


def getStationCoordinates(databseFile, StationID):
    connection = sqlite3.connect(databseFile)
    cursor = connection.cursor()
    cursor.execute("""
        SELECT Latitude, Longitude 
        FROM Stations
        WHERE NaPTAN = ?
    """, (StationID, ))
    coordinates = cursor.fetchall()[0]
    connection.close()
    return coordinates


def SaveTfLData(databaseFile, TfL_API_KEY):
    stationDictionary, linesDictionary = fetchTfLData(databaseFile, TfL_API_KEY)
    connection = sqlite3.connect(databaseFile)
    cursor = connection.cursor()

    for station in stationDictionary.values():
        NaPTAN = station.NaPTAN
        StationName = station.StationName
        Latitude = station.Latitude
        Longitude = station.Longitude
        cursor.execute("""
            INSERT OR REPLACE INTO Stations (NaPTAN, StationName, Latitude, Longitude) 
            VALUES (?, ?, ?, ?)
            """, (NaPTAN, StationName, Latitude, Longitude))
        connection.commit()

    for line in linesDictionary.keys():
        LineID = line
        branches = linesDictionary[line]
        for branch in branches:
            for i in range(len(branch) - 1):
                StationA = branch[i]
                StationB = branch[i + 1]

                cursor.execute("""
                    SELECT AverageSpeed
                    From Lines
                    WHERE LineID = ?
                """, (LineID,))
                AverageSpeed = float(cursor.fetchall()[0][0])

                stationACoordinates = getStationCoordinates(databaseFile, StationA)
                stationBCoordinates = getStationCoordinates(databaseFile, StationB)
                distanceKM = geodesic(stationACoordinates, stationBCoordinates).km
                BaseTravelTime = (distanceKM / AverageSpeed) * 60

                # So that reverse is possible
                cursor.execute("""
                    INSERT OR REPLACE INTO Connections (StationA, StationB, LineID, BaseTravelTime)
                    VALUES (?, ?, ?, ?)
                    """, (StationA, StationB, LineID, BaseTravelTime))
                cursor.execute("""
                    INSERT OR REPLACE INTO Connections (StationA, StationB, LineID, BaseTravelTime)
                    VALUES (?, ?, ?, ?)
                    """, (StationB, StationA, LineID, BaseTravelTime))

    connection.commit()
    connection.close()

    getStationLineRelationships(databaseFile)


def main(TFL_API_KEY, databaseFile):
    SaveTfLData(databaseFile, TFL_API_KEY)



if __name__ == "__main__":
    TfL_API_KEY = "0ff5a2076cd640cb957e63d6947efc61"
    main(TfL_API_KEY, "final.db")
    pass