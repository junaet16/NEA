from opencage.geocoder import OpenCageGeocode
from sqlalchemy import create_engine
import json
from sqlalchemy.orm import Session
import models
from test_concepts.models import VenueModel


def getCoordinates(key, location):
    geocoder = OpenCageGeocode(key)
    results = geocoder.geocode(location)[0]["geometry"]
    return results


def getStadiumData(londonClubsFile, databaseFile, key):
    with open(londonClubsFile, "r") as file:
        londonClubs = json.load(file)

    for club, data in londonClubs.items():
        stadiumName, capacity = data
        coordinates = getCoordinates(key, stadiumName)
        insertData(databaseFile, club, stadiumName, capacity, coordinates)
        print(club, stadiumName, capacity, coordinates)
    print("Give up")


def insertData(databaseFile, club, stadiumName, capacity, coordinates):
    engine = create_engine(f"sqlite:///{databaseFile}")
    models.Base.metadata.create_all(engine)

    latitude = coordinates["lat"]
    longitude = coordinates["lng"]

    with Session(engine) as session:
        team = models.TeamModel(
            TeamName = stadiumName,
            VenueName = club,
        )
        session.merge(team)

        venue = models.VenueModel(
            VenueName = stadiumName,
            Capacity = capacity,
            Latitude = latitude,
            Longitude = longitude
        )
        session.merge(venue)

        session.commit()


def main():
    key = "eb0e2c9b71cc45f7aafe0ae4ecc44cc2"
    londonClubsFile = "londonClubs.json"
    databaseFile = "final.db"
    getStadiumData(londonClubsFile, databaseFile, key)


if __name__ == '__main__':
    main()