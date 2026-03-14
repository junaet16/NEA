import sqlite3
import classes
from customFunctions import safeGet
from geopy.distance import geodesic


#GLOBAL PARAMETERS
#How long a train waits at a station
WAITING_TIME = 0.5


# Creates a dictionary with the format - {NaPTAN : Station object}
# Fetches all stations served by the given LineIDs from the TfL API
def fetchStations(TfL_API_KEY, lineIDs):
    stationDictionary = {}
    params = {
        "app_key": TfL_API_KEY,
    }

    # Loop through every line stored in the database
    for line in lineIDs:
        url = f"https://api.tfl.gov.uk/Line/{line}/Route/Sequence/inbound"
        response = safeGet(url, params=params)
        if type(response) is int: #Checks if there has been an error
            return response
        data = response.json()
        stations = data["stations"]

        # Create a CreationStation object for every unique station
        for station in stations:
            if station["id"] not in stationDictionary:  # So every entry is unique
                NaPTAN = station['id']
                StationName = station['name']
                Latitude = station['lat']
                Longitude = station['lon']

                # CreationStation extends Station and stores geographic coordinates
                stationDictionary[station["id"]] = classes.CreationStation(NaPTAN, StationName, Latitude, Longitude)

    return stationDictionary


# Uses a list of LineIDs and a list of Station objects to create a dictionary in the form {LineID : [[Branch1], [Branch2], ..., [Branchn]]
def fetch_lines(stationDictionary, TfL_API_KEY, lineIDs):
    linesDictionary = {}  # Final dictionary that will be returned
    # Some stations are returned strangely by the API (different IDs for different branches)
    # This dictionary maps incorrect IDs to their correct hub NaPTAN IDs
    weirdStations = {} # {incorrectID : correctID}
    params = {
        "app_key": TfL_API_KEY,
    }

    # Loop through each LineID
    for line in lineIDs:
        url = f"https://api.tfl.gov.uk/Line/{line}/Route/Sequence/inbound"
        response = safeGet(url, params=params)
        if type(response) is int: #Checks if there has been an error
            return response
        data = response.json()
        branches = data["orderedLineRoutes"]
        listOflistsOfNAPTAN = []

        # Each branch represents one possible ordered path of stations on the line
        for branchAllData in branches:
            # branchAllData contains additional metadata which is not needed
            branch = branchAllData["naptanIds"]  # List of all stations (NaPTAN IDs) of the branch
            for i, id in enumerate(branch):
                if id not in stationDictionary:  # All possible unique stations already exist in stationDictionary, but some stations have other IDs for different modes, which means they need to be filtered out so that there is only one ID per station
                    if id not in weirdStations:  # Store of all the stations that have different IDs
                        # Fetch station details to find its hub NaPTAN ID
                        newURL = f"https://api.tfl.gov.uk/StopPoint/{id}"  # Fetches all data for me regarding that particular station
                        newResponse = safeGet(newURL, params=params)
                        newData = newResponse.json()
                        newId = newData["hubNaptanCode"]  # Collects the ID that represents the entire station and not just that mode/line
                        # Store mapping so future lookups don't require another API call
                        weirdStations[id] = newId

                    # Replace incorrect ID with correct hub ID
                    id = weirdStations[id]
                    branch[i] = id  # Changes the ID of the station in the branch to the correct ID

            # Add the cleaned branch to the list of branches for this line
            listOflistsOfNAPTAN.append(branch)

        linesDictionary[line] = listOflistsOfNAPTAN

    return linesDictionary


# Fetches all TfL data for me required to populate the database (that can be gotten from the TfL API)
# Returns stationDictionary and linesDictionary
def fetchTfLData(databaseFile, TfL_API_KEY):
    connection = sqlite3.connect(databaseFile)
    cursor = connection.cursor()

    # Creates a list of LineIDs
    linesCursorObject = cursor.execute("SELECT LineID FROM Lines")
    lineIDs = []
    for lineTuple in linesCursorObject:  # SQL returns data for me in the form (LineID,)
        lineIDs.append(lineTuple[0])

    # Fetch all stations served by the stored lines
    stationDictionary = fetchStations(TfL_API_KEY, lineIDs)
    print("Fetched Stations")

    # Fetch ordered branches for each line
    linesDictionary = fetch_lines(stationDictionary, TfL_API_KEY, lineIDs)
    print("Fetched Lines")

    connection.close()
    return stationDictionary, linesDictionary


# Puts every possible Station, Line pair into the StationLineRelationships table
# Acts as the joining table between Stations and Lines
def getStationLineRelationships(databseFile):
    connection = sqlite3.connect(databseFile)
    cursor = connection.cursor()

    # Use the Connections table to get which stations are served by which lines
    rows = cursor.execute("SELECT StationA, LineID from Connections").fetchall()
    for row in rows:
        StationA = row[0]
        LineID = row[1]

        # Ignore as well because station might have more than 1 connection to another station via the same line -- different branch lines are given start to end, which therefore means sometimes multiple of the same connection are attempted to be stored
        cursor.execute("""
            INSERT OR REPLACE INTO StationLineRelationships (NaPTAN, LineID) 
            VALUES (?, ?)
            """, (StationA, LineID))

    connection.commit()
    connection.close()


# Fetches the latitude and longitude of a station from the database
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


# Stores all fetched TfL data for me into the database
# Populates Stations, Connections, and StationLineRelationships tables
#Print statements for testing purposes
def SaveTfLData(databaseFile, TfL_API_KEY):
    stationDictionary, linesDictionary = fetchTfLData(databaseFile, TfL_API_KEY)

    # Stop execution if an API error occurred
    if type(stationDictionary) is int or type(linesDictionary) is int:
        print(f"A {stationDictionary} error has occurred")
        return stationDictionary

    print("TfL Data Fetched")
    connection = sqlite3.connect(databaseFile)
    cursor = connection.cursor()

    # Store all stations in the Stations table
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
    print("Stored Stations")

    # Store all connections between adjacent stations on each line
    for line in linesDictionary.keys():
        LineID = line
        branches = linesDictionary[line]
        for branch in branches:
            # Adjacent stations form edges in the transport graph
            for i in range(len(branch) - 1):
                StationA = branch[i]
                StationB = branch[i + 1]

                # Fetch average speed of the line from the database
                cursor.execute("""
                    SELECT AverageSpeed
                    From Lines
                    WHERE LineID = ?
                """, (LineID,))
                AverageSpeed = float(cursor.fetchall()[0][0])

                # Fetch station coordinates
                stationACoordinates = getStationCoordinates(databaseFile, StationA)
                stationBCoordinates = getStationCoordinates(databaseFile, StationB)

                # Calculate distance and base travel time (no crowding)
                distanceKM = geodesic(stationACoordinates, stationBCoordinates).km

                # Add a default minute penalty to represent the time trains wait at a station
                BaseTravelTime = ((distanceKM / AverageSpeed) * 60) + WAITING_TIME

                # Store connections in both directions
                cursor.execute("""
                    INSERT OR REPLACE INTO Connections (StationA, StationB, LineID, BaseTravelTime)
                    VALUES (?, ?, ?, ?)
                    """, (StationA, StationB, LineID, BaseTravelTime))
                cursor.execute("""
                    INSERT OR REPLACE INTO Connections (StationA, StationB, LineID, BaseTravelTime)
                    VALUES (?, ?, ?, ?)
                    """, (StationB, StationA, LineID, BaseTravelTime))

    print("Stored connections")

    connection.commit()
    connection.close()

    # Populate StationLineRelationships using stored connections
    getStationLineRelationships(databaseFile)

    return True


#Main function
def main(TFL_API_KEY, databaseFile):
    code = SaveTfLData(databaseFile, TFL_API_KEY)
    if type(code) is int:
        print(f"A {code} error has occurred")
        return code
    return True



if __name__ == "__main__":
    TfL_API_KEY = "0ff5a2076cd640cb957e63d6947efc61"
    main(TfL_API_KEY, "final.db")
    pass