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


#Returns the approximate time of the middle of the journey (without consideration of delays and things)
def calculateDefaultMidjourneyTime(baseInputData, databaseFile, CHANGING_TIME):
    journeyStart = baseInputData["journeyStart"]
    startStation = baseInputData["startStation"]
    endStation = baseInputData["endStation"]

    graph = MakeGraph(databaseFile)
    steps = Dijkstra(graph, startStation, endStation, CHANGING_TIME)
    print(steps)
    totalMinutes = steps[-1][3] #steps is in the form [[PreviousStationNaPTAN, NextStationNaPTAN, lineID, LengthOfTimeToPoint],...]
    halfMinutes = totalMinutes // 2

    timeObject = datetime.datetime.strptime(journeyStart, "%H:%M")
    timeDelta = datetime.timedelta(minutes=halfMinutes)
    timeObject += timeDelta

    return timeObject


#As the name suggests, it returns the list of events in the timeframe in which an event might impact the journey - I might change the format of the returned data later
def findEventsInTimeFrame(midjourneyTime, databaseFile, baseInputData, MAX_TIME_WINDOW, arrivalPeakOffset, departurePeakOffset):
    connection = sqlite3.connect(databaseFile)
    cursor = connection.cursor()
    date = baseInputData["date"]
    importantEvents = {} #(venue, date) : minuteDifference  - The events which might affect the journey

    #Fetches all the events in that day
    eventsInDay = cursor.execute("""
        SELECT *
        FROM Events
        WHERE Date = ?
        """, (date,)).fetchall()

    #Event is in the form [VenueName, Date, Time, HomeTeam, AwayTeam, EventName, Duration]
    for event in eventsInDay:
        duration = event[6]
        eventTime = datetime.datetime.strptime(event[2], "%H:%M")
        endTime = eventTime + datetime.timedelta(minutes=duration)

        startTimeDifference = abs(eventTime - arrivalPeakOffset - midjourneyTime) #Peaks are unlikely to be immediately at the start or end of an event
        endTimeDifference = abs((endTime + departurePeakOffset) - midjourneyTime)

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


#This function assigns each station a weight so that the number of people at the stations will be more accurately assigned
#stationDistances dictionary format - {NaPTAN: distance}
#Returns dictionary format - {NaPTAN: proportion}
def inverseWeight(stationDistances):
    extra = 1 #Avoid divide by zero errors - if the distance between the station and the venue is 0
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


#Returns the proportion of the peak expected number of people at a station at the given time
def gausianFactorAtPeak(relativePeak, sigma, relativeTimeDifference):
    x = (relativePeak - relativeTimeDifference) / sigma
    returnFactor = math.exp(-0.5 * x * x)
    return returnFactor


#For each event, finds the base number of people at the nearby stations
def findBaseNumberOfPeople(
        capacity,
        ATTENDANCE, #The proportion of seats that will actually be filled
        TRAIN_PROPORTION, #The proportion of people using TfL rail
        startDifferenceMinutes, #minutes from journey midpoint to event start
        endDifferenceMinutes, #minutes from journey midpoint to event end
        arrivalWindowMinutes, #Length of time of arrival window where the journey may be affected
        departureWindowMinutes, #Length of time of departure window where the journey may be affected
        arrivalPeakOffset, #Offset because peaks are usually not at exactly the start or end
        departurePeakOffset,
        statonsWithDistances, #Dictionary of stations with the values being the distance between the station and the station and the venue
        MAX_TIME_WINDOW,
        SIGMA_FACTOR,
):

    totalAttendance = capacity * ATTENDANCE #Gets the expected attendance at the venue
    tflUsageTotal = totalAttendance * TRAIN_PROPORTION #Gets the expected total usage of TfL rail

    proportions = inverseWeight(statonsWithDistances)
    StationsWithPeopleAtPeak = {}
    for stationID in proportions.keys():
        StationsWithPeopleAtPeak[stationID] = proportions[stationID] * tflUsageTotal

    relativeArrivalPeakTime = startDifferenceMinutes - arrivalPeakOffset
    relativeDepartPeakTime = endDifferenceMinutes + departurePeakOffset

    sigmaArrival = max(1, arrivalWindowMinutes / SIGMA_FACTOR) #max used to make sure sigma is at least bigger or equal to 1
    sigmaDeparture = max(1, departureWindowMinutes / SIGMA_FACTOR)

    #Realistically there isn't going to be a difference between arrival and departure rates because if you came by train, you will probably leave by train so will not affect, and vice versa, so the factors will be set to one

    arrivalsFactorAtMid = gausianFactorAtPeak(relativeArrivalPeakTime, sigmaArrival, 0)
    depratureFactorAtMid = gausianFactorAtPeak(relativeDepartPeakTime, sigmaDeparture, 0)

    stationsAtMid = {} #Format - {NaPTAN: ArrivalNumbers, DepartureNumbers}
    for stationID in StationsWithPeopleAtPeak.keys():
        arrivalPeople = StationsWithPeopleAtPeak[stationID] * arrivalsFactorAtMid
        departurePeople = StationsWithPeopleAtPeak[stationID] * depratureFactorAtMid
        stationsAtMid[stationID] = [arrivalPeople, departurePeople]

    return stationsAtMid



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