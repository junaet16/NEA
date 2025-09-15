#Creating temporary fake data for testing purposes
import sqlite3

def fake_events_and_stadium():
    connection = sqlite3.connect('nea.db')
    cursor = connection.cursor()
    #Use JSON instead of a list of stuff?
    #Create tables
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS venue (
        nameID TEXT PRIMARY KEY,
        venueName TEXT,
        teamID TEXT,
        capacity INTEGER,
        stationsNearby TEXT,
        coordinates TEXT)
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS events (
    venueID TEXT,
    eventName TEXT,
    dateOfEvent TEXT,
    timeOfEvent TEXT,
    homeTeamID TEXT,
    awayTeamID TEXT,
    PRIMARY KEY(venueID, dateOfEvent)
    FOREIGN KEY(venueID) REFERENCES venue(nameID)
    )""")

    venuesList = [
        ("Emirates", "Emirates Stadium", "ARS", 60704, "940GZZLUASL", "N/A")
    ]

    cursor.executemany("""
    INSERT INTO venue (nameID, venueName, teamID, capacity, stationsNearby, coordinates)
    VALUES (?, ?, ?, ?, ?, ?)""", venuesList)

    eventsList = [
        ("Emirates", "Example", "23/12/2025", "13:00", "ARS", "TOT")
    ]

    cursor.executemany("""
    INSERT INTO events (venueID, eventName, dateOfEvent, timeOfEvent, homeTeamID, awayTeamID)
    VALUES (?, ?, ?, ?, ?, ?)
    """, eventsList)

    connection.commit()
    connection.close()



def takeInput():
    #For now it will just return a default value for testing purposes?
    if input("Use custom? y/n: ") == "y":
        pass #late
    else:
        pass #Will work on it later









def main():
    fake_events_and_stadium()

if __name__ == '__main__':
    main()
