import sqlite3
from test_big import MakeGraph, Dijkstra
import datetime
import math
import collections

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
        duration = event[6]
        eventTime = datetime.datetime.strptime(event[2], "%H:%M")
        endTime = eventTime + datetime.timedelta(minutes=duration)
        startTimeDifference = abs(eventTime - midjourneyTime)
        endTimeDifference = abs(endTime - midjourneyTime) #I'll do the offset stuff here
        if startTimeDifference > endTimeDifference:
            timeDifference = endTimeDifference
        else:
            timeDifference = startTimeDifference
        minutesDifference = timeDifference.total_seconds() // 60
        if minutesDifference <= MAX_TIME_WINDOW:
            venue = event[0]
            startDifferenceMinutes = startTimeDifference.total_seconds() // 60
            endDifferenceMinutes = endTimeDifference.total_seconds() // 60
            importantEvents[(venue, date)] = [minutesDifference, startDifferenceMinutes, endDifferenceMinutes]

    connection.close()
    return importantEvents


#stationDistances dictionary format - {NaPTAN: distance}
def inverseWeight(stationDistances):
    extra = 0 #Avoid divide by zero errors - for testing purposes I'll ignore it and put 0
    weights = {}
    proportions = {}
    totalWeight = 0
    for station in stationDistances.keys():
        distance = stationDistances[station]
        weight = 1 / (distance + extra)
        totalWeight += weight
        weights[station] = weight

    for station in weights.keys():
        proportion = weights[station] / totalWeight
        proportions[station] = proportion

    return proportions


def returnStationsWithDistances():
    #Ok the actual one will with Google Maps API and stuff but for now I will just return a default value
    stationsWithDistances = {"940GZZLUASL":200, "HUBHHY": 300, "940GZZLUHWY":500}
    return stationsWithDistances


#Unfinished
def findBaseNumberOfPeople(
        capacity,
        ATTENDANCE,
        TRAIN_PROPORTION,
        statonsWithDistances,
        MAX_TIME_WINDOW,
        SIGMA_FACTOR
):
    totalAttendance = capacity * ATTENDANCE
    tflUsageTotal = totalAttendance * TRAIN_PROPORTION
    peakProportion = tflUsageTotal / capacity
    proportions = inverseWeight(statonsWithDistances)
    calculationSIGMA = max(1, MAX_TIME_WINDOW / SIGMA_FACTOR) #max used to make sure sigma is at least bigger or equal to 1



def main():
    databaseFile = "test.db"
    CHANGING_TIME = 3
    MAX_TIME_WINDOW = 120
    ATTENDANCE = 1.0 #Percentance of the stadium full
    TFL_ATTENDANCE = 1.0 #The number of event attendees using TFL rail services
    PEAK_FRACTION = 0.5 #The percentage of the total number of unique people who will pass through the station, at the peak time
    baseInputData = takeInput()
    midTimeObject = calculateDefaultMidjourneyTime(baseInputData, databaseFile, CHANGING_TIME)
    events = findEventsInTimeFrame(midTimeObject, databaseFile, baseInputData, MAX_TIME_WINDOW)
    print(events)


if __name__ == '__main__':
    main()