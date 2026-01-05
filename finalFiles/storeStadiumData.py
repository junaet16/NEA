import sqlite3
from opencage.geocoder import OpenCageGeocode
import json
from geopy.distance import geodesic


#Use of the API to get coordinates
def getCoordinates(key, location):
    geocoder = OpenCageGeocode(key)
    results = geocoder.geocode(location)[0]["geometry"] #Where you can get the coordinates
    return results


def getCloseStations(allStations, venueCoordinates, walkingDistance):
    stationWithDistance = []
    CloseStationDictionary = {}

    for stationTuple in allStations:
        stationCoordinates = (stationTuple[1], stationTuple[2])
        distanceKM = geodesic(venueCoordinates, stationCoordinates).km
        stationWithDistance.append((stationTuple[0], distanceKM))
    stationWithDistance.sort(key=lambda x: x[1])

    firstStation = stationWithDistance.pop(0)
    CloseStationDictionary[firstStation[0]] = firstStation[1]

    for station in stationWithDistance:
        if station[1] <= walkingDistance:
            CloseStationDictionary[station[0]] = station[1]

    return CloseStationDictionary


#Inserts data into database for every club
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

    closeStations = getCloseStations(allStations, venueCoordinates, walkingDistance)

    for stationID in closeStations.keys():
        distance = closeStations[stationID]
        cursor.execute("""
            INSERT INTO VenueStationRelationships
            VALUES (?, ?, ?)
            ON CONFLICT (VenueName, NaPTAN) DO
                UPDATE SET
                    Distance = excluded.Distance
        """, (stadiumName, stationID, distance))

    cursor.execute("""
        INSERT INTO Teams (TeamName, VenueName)
        VALUES (?, ?)
        ON CONFLICT (TeamName)
            DO UPDATE SET
                VenueName = excluded.VenueName
    """, (club, stadiumName))

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


#Uses JSON file of club data
#{"ClubName" : [StadiumName, Capacity]}
def getStadiumData(londonClubsFile, databaseFile, key, walkingDistance):
    with open(londonClubsFile, "r") as file:
        londonClubs = json.load(file)

    for club, data in londonClubs.items():
        stadiumName, capacity = data
        try:
            coordinates = getCoordinates(key, stadiumName)
        except:
            return "Opencage Geocoder API"
        insertData(databaseFile, club, stadiumName, capacity, coordinates, walkingDistance)

    return True


def calculateWalkingDistance(walkingTime, walkingSpeed):
    distance = (walkingSpeed * walkingTime) / 60
    return distance


def main(key, londonClubsFile, databaseFile, walkingTime, walkingSpeed):
    walkingDistance = calculateWalkingDistance(walkingTime, walkingSpeed)
    done = getStadiumData(londonClubsFile, databaseFile, key, walkingDistance)
    print(done)
    return done


def redoStore(walkingTime, walkingSpeed, londonClubsFile, databaseFile):
    walkingDistance = calculateWalkingDistance(walkingTime, walkingSpeed)

    with open(londonClubsFile, "r") as file:
        londonClubs = json.load(file)

    connection = sqlite3.connect(databaseFile)
    cursor = connection.cursor()
    cursor.execute("DELETE FROM VenueStationRelationships")
    connection.commit()
    connection.close()

    for club, data in londonClubs.items():
        stadiumName, capacity = data

        connection = sqlite3.connect(databaseFile)
        cursor = connection.cursor()

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