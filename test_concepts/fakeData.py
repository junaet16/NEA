import sqlite3


def fakeVenues(database):
    connection = sqlite3.connect(database)
    cursor = connection.cursor()
    venuesList = [
        ("Emirates Stadium", 60704, 0, 0)
    ]

    for venue in venuesList:
        cursor.execute("""
            INSERT INTO Venues (VenueName, Capacity, Latitude, Longitude)
            VALUES (?, ?, ?, ?)""", venue)

    connection.commit()
    connection.close()


def fakeEvents(database):
    connection = sqlite3.connect(database)
    cursor = connection.cursor()
    eventsList = [
        ("Emirates Stadium", "12/12/2026", "14:00", "Arsenal", "Tottenham", "N/A")
    ]

    for event in eventsList:
        cursor.execute("""
            INSERT INTO Events (VenueName, Date, Time, HomeTeam, AwayTeam, EventName)
            Values (?, ?, ?, ?, ?, ?)""", event)

    connection.commit()
    connection.close()


def main():
    database = "test.db"
    fakeVenues(database)
    fakeEvents(database)


if __name__ == '__main__':
    main()