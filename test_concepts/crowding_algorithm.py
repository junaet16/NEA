import sqlite3
from test_big import MakeGraph, Dijkstra
import datetime

def takeInput():
    #For testing purposes this will now be a default value
    date = "12/12/2026"
    journeyStart = "13:00"
    startStation = "940GZZLULYS"
    endStation = "HUBSRA"

    data = {
        "date": date,
        "journeyStart": journeyStart,
        "startStation": startStation,
        "endStation": endStation
    }

    return data


def calculateDefaultMidjourneyTime(baseInputData, databaseFile, CHANGING_TIME):
    journeyStart = baseInputData["journeyStart"]
    startStation = baseInputData["startStation"]
    endStation = baseInputData["endStation"]

    graph = MakeGraph(databaseFile)
    steps = Dijkstra(graph, startStation, endStation, CHANGING_TIME)
    totalMinutes = steps[-1][3]
    halfMinutes = totalMinutes // 2

    timeObject = datetime.datetime.strptime(journeyStart, "%H:%M")
    timeDelta = datetime.timedelta(minutes=halfMinutes)
    timeObject += timeDelta

    return timeObject


def findEventsInTimeFrame(midjourneyTime, databaseFile, baseInputData, MAX_TIME_WINDOW):
    connection = sqlite3.connect(databaseFile)
    cursor = connection.cursor()
    date = baseInputData["date"]
    importantEvents = {} #(venue, date) : minuteDifference

    eventsInDay = cursor.execute("""
        SELECT *
        FROM Events
        WHERE Date = ?
        """, (date,)).fetchall()

    for event in eventsInDay:
        eventTime = datetime.datetime.strptime(event[2], "%H:%M")
        timeDifference = abs(eventTime - midjourneyTime)
        minutesDifference = timeDifference.total_seconds() // 60
        if minutesDifference <= MAX_TIME_WINDOW:
            venue = event[0]
            importantEvents[(venue, date)] = minutesDifference

    connection.close()
    return importantEvents


def findBaseNumberOfPeople():
    pass


def main():
    databaseFile = "test.db"
    CHANGING_TIME = 3
    MAX_TIME_WINDOW = 120
    baseInputData = takeInput()
    midTimeObject = calculateDefaultMidjourneyTime(baseInputData, databaseFile, CHANGING_TIME)
    events = findEventsInTimeFrame(midTimeObject, databaseFile, baseInputData, MAX_TIME_WINDOW)
    print(events)


if __name__ == '__main__':
    main()