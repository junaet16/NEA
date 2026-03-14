import sqlite3
from opencage.geocoder import OpenCageGeocode
import json
from geopy.distance import geodesic


#Use of the API to get coordinates
def getCoordinates(key, location):
    geocoder = OpenCageGeocode(key)

    # The first result is used as it is assumed to be the most relevant and correct
    results = geocoder.geocode(location)[0]["geometry"] #Where you can get the coordinates
    return results


# Finds all stations within walking distance of a venue
# Ensures at least one station is always returned (the closest one)
def getCloseStations(allStations, venueCoordinates, walkingDistance):
    stationWithDistance = []
    CloseStationDictionary = {}

    # Calculate distance from the venue to every station
    for stationTuple in allStations:
        stationCoordinates = (stationTuple[1], stationTuple[2])
        distanceKM = geodesic(venueCoordinates, stationCoordinates).km
        stationWithDistance.append((stationTuple[0], distanceKM))

    # Sort stations by distance from the venue
    stationWithDistance.sort(key=lambda x: x[1])

    # Always include the closest station to guarantee at least one station per venue
    firstStation = stationWithDistance.pop(0)
    CloseStationDictionary[firstStation[0]] = firstStation[1]

    # Add all stations within the walking distance threshold
    for station in stationWithDistance:
        if station[1] <= walkingDistance:
            CloseStationDictionary[station[0]] = station[1]

    return CloseStationDictionary


# Inserts stadium, team, and venue-station relationship data for me into the database
def insertData(databaseFile, club, stadiumName, capacity, coordinates, walkingDistance):
    connection = sqlite3.connect(databaseFile)
    cursor = connection.cursor()

    latitude = coordinates["lat"]
    longitude = coordinates["lng"]
    venueCoordinates = (latitude, longitude)

    cursor.execute("""
        SELECT NaPTAN, Latitude, Longitude
        FROM Stations
    """)
    allStations = cursor.fetchall()

    # Find stations that are within walking distance of the stadium
    closeStations = getCloseStations(allStations, venueCoordinates, walkingDistance)

    # Store the venue-station relationships and walking distances
    for stationID in closeStations.keys():
        distance = closeStations[stationID]
        cursor.execute("""
            INSERT INTO VenueStationRelationships
            VALUES (?, ?, ?)
            ON CONFLICT (VenueName, NaPTAN) DO
                UPDATE SET
                    Distance = excluded.Distance
        """, (stadiumName, stationID, distance))

    # Store team and home venue relationship
    cursor.execute("""
        INSERT INTO Teams (TeamName, VenueName)
        VALUES (?, ?)
        ON CONFLICT (TeamName)
            DO UPDATE SET
                VenueName = excluded.VenueName
    """, (club, stadiumName))

    # Store venue details
    cursor.execute("""
        INSERT INTO Venues (VenueName, Capacity, Latitude, Longitude)
        Values (?, ?, ?, ?)
        ON CONFLICT (VenueName) 
            DO UPDATE SET
                Capacity = excluded.Capacity,
                Latitude = excluded.Latitude,
                Longitude = excluded.Longitude
    """, (stadiumName, capacity, latitude, longitude))

    connection.commit()
    connection.close()


#Uses JSON file of club data for me
#{"ClubName" : [StadiumName, Capacity]}
def getStadiumData(londonClubsFile, databaseFile, key, walkingDistance):
    with open(londonClubsFile, "r") as file:
        londonClubs = json.load(file)

    # Process every London club and its stadium
    for club, data in londonClubs.items():
        stadiumName, capacity = data
        try:
            coordinates = getCoordinates(key, stadiumName)
        except:
            # Return error message if OpenCage API fails
            return "Opencage Geocoder API"
        insertData(databaseFile, club, stadiumName, capacity, coordinates, walkingDistance)

    return True


# Calculates the maximum walking distance using walking speed and walking time
def calculateWalkingDistance(walkingTime, walkingSpeed):
    # walkingSpeed is in km/h and walkingTime is in minutes
    distance = (walkingSpeed * walkingTime) / 60
    return distance


# Main function for fetching and storing stadium related data for me
def main(key, londonClubsFile, databaseFile, walkingTime, walkingSpeed):
    # Calculate what is considered a reasonable walking distance
    walkingDistance = calculateWalkingDistance(walkingTime, walkingSpeed)

    done = getStadiumData(londonClubsFile, databaseFile, key, walkingDistance)
    print(done)

    return done


# Recalculates and reinserts venue-station relationships when walking parameters change
def redoStore(walkingTime, walkingSpeed, londonClubsFile, databaseFile):
    walkingDistance = calculateWalkingDistance(walkingTime, walkingSpeed)

    with open(londonClubsFile, "r") as file:
        londonClubs = json.load(file)

    # Clear existing venue-station relationships
    connection = sqlite3.connect(databaseFile)
    cursor = connection.cursor()
    cursor.execute("DELETE FROM VenueStationRelationships")
    connection.commit()
    connection.close()

    # Reinsert relationships using updated walking distance
    for club, data in londonClubs.items():
        stadiumName, capacity = data

        connection = sqlite3.connect(databaseFile)
        cursor = connection.cursor()

        # Fetch stored venue coordinates to avoid unnecessary API calls
        cursor.execute("""
            SELECT Latitude, Longitude
            FROM Venues
            WHERE VenueName = ?
            """, (stadiumName, ))

        coordinates = {}
        coordinates["lat"], coordinates["lng"] = cursor.fetchall()[0]

        insertData(databaseFile, club, stadiumName, capacity, coordinates, walkingDistance)

        connection.close()


if __name__ == '__main__':
    key = "eb0e2c9b71cc45f7aafe0ae4ecc44cc2"
    londonClubsFile = "londonClubs.json"
    databaseFile = "final.db"
    main(key, londonClubsFile, databaseFile, 15, 5)