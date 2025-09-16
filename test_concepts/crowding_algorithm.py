import sqlite3




#I realised I need to fundamentally change the Dijkstra's and making graph functions soooooooooooooooooo thats the task for at home :sob



def fake_events_and_stadium():
    connection = sqlite3.connect('nea.db')
    cursor = connection.cursor()
    #Use JSON instead of a list of stuff?
    #Create tables

    kill = ["DROP TABLE IF EXISTS venues", "DROP TABLE IF EXISTS events"]

    for thingToKill in kill:
        cursor.execute(thingToKill)


    cursor.execute("""
    CREATE TABLE IF NOT EXISTS venues (
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
    FOREIGN KEY(venueID) REFERENCES venues(nameID)
    )""")
#Test

    venuesList = [
        ("Emirates", "Emirates Stadium", "ARS", 60704, "940GZZLUASL", "N/A")
    ]

    cursor.executemany("""
    INSERT INTO venues (nameID, venueName, teamID, capacity, stationsNearby, coordinates)
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
        start = "940GZZLULYS"
        end = "940GZZLUBOS"
        date = "23/12/2025"
        starTime = "14:00"


def calculateMidJourney(unprocessedInput):
    pass









def main():
    fake_events_and_stadium()
    unprocessedInput = takeInput()
    finalInput = calculateMidJourney(unprocessedInput)

if __name__ == '__main__':
    main()
