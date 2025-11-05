from pathFinding import MakeGraph, Dijkstra
import datetime
import sqlite3
import math
import models
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import classes


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

#Testin
#Test 2
#Returns the approximate time of the middle of the journey (without consideration of delays and things)
def calculateDefaultMidjourneyTime(baseInputData, databaseFile, CHANGING_TIME):
    journeyStart = baseInputData["journeyStart"]
    startStation = baseInputData["startStation"]
    endStation = baseInputData["endStation"]

    graph = MakeGraph(databaseFile)
    steps = Dijkstra(graph, startStation, endStation, CHANGING_TIME)
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


#For each event, finds the base number of people at the nearby stations at the middle of the journey
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
        SIGMA_FACTOR
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


def findCapacity(databaseFile, VenueName):
    engine = create_engine(f"sqlite:///{databaseFile}")
    Session = sessionmaker(bind=engine)
    session = Session()
    venue = session.query(models.VenueModel).filter(models.VenueModel.VenueName == VenueName).first()
    return venue.Capacity


#Recursion???????
def propegation(graph, stationID, people, MINIMUM_PEOPLE, network, event, PROPEGATION_FACTOR):
    stationObject = network.nodes[stationID] #Fetches the Dijkstra station object stored in the network 
    if stationObject.IsAffected() == False:
        NaPTAN = stationID
        StationName = stationObject.StationName
        #Above lines fetch the information stored in the old object
        newStationObject = classes.AffectedDijkstraStation(NaPTAN, StationName) #Creates a new affected object
        newStationObject.events[event] = people #Adds the number of people at this station because of this event
        stationObject = newStationObject
        network.nodes[stationID] = stationObject #Replaces old object
    try:
        oldPeople = stationObject.events[event] #This will work If and only if the station was already affected by this event
    except:
        oldPeople = 0 #This will run if the station has been already affected but not by this event so the event can't be found in the object, so the old population will be set as 0
    if oldPeople > people:
        pass #No need to update because a larger wave of people have passed through already. Propegration will not be needed because a larger wave existed which has been propegated already
    else:
        stationObject.events[event] = people
        network.nodes[stationID] = stationObject #Updates the people at this station due to this event at this station
        newPeople = people * PROPEGATION_FACTOR
        if newPeople < MINIMUM_PEOPLE:
            pass
        else:
            connections = graph[stationID]
            for connection in connections:
                newStationID = connection[0]
                propegation(graph, newStationID, newPeople, MINIMUM_PEOPLE, network, event, PROPEGATION_FACTOR)


#Creates a parameter object to store the parameters used for calculation
def getParameters(username, databaseFile):
    #Real one will get from database
    CHANGING_TIME = 3
    MAX_TIME_WINDOW = 120
    rawArrivalPeakOffset = 15
    rawDeparturePeakOffset = 15
    ATTENDANCE = 1.0 #Percentance of the stadium full
    TRAIN_PROPORTION = 1 #The number of event attendees using TFL rail services
    SIGMA_FACTOR = 4
    MINIMUM_PEOPLE = 50 #The minimum number of people for a station to be considered affected
    PERSON_DELAY = 0.002 #Percentage delay increase per extra person
    PROPEGATION_FACTOR = 0.5

    parameterObject = classes.Parameters(
        CHANGING_TIME,
        MAX_TIME_WINDOW,
        rawArrivalPeakOffset,
        rawDeparturePeakOffset,
        ATTENDANCE,
        TRAIN_PROPORTION,
        SIGMA_FACTOR,
        MINIMUM_PEOPLE,
        PERSON_DELAY,
        PROPEGATION_FACTOR
    )

    parameterObject.calculateWindow()
    parameterObject.calculatePeakOffset()
    parameterObject.calculateMinutesOffset()

    return parameterObject


#Creates NotAffectedStation and NotAffectedConnection objects which are then stored in the dictionaries
def createConnection(baseGraph, session, stations, connections, network):
    for StationA in baseGraph.keys():
        stationInfo = session.query(models.StationModel).filter(models.StationModel.NaPTAN == StationA).first()
        NaPTAN = StationA
        StationName = stationInfo.StationName
        TravelZone = stationInfo.TravelZone
        baseStationClass = classes.NotAffectedDijkstraStation(NaPTAN, StationName, TravelZone)
        stations[StationA] = baseStationClass

        for connection in baseGraph[StationA]:
            StationA = StationA
            StationB = connection[0]
            BaseTravelTime = connection[1]
            LineID = connection[2]
            baseConnectionClass = classes.NotAffectedConnection(StationA, StationB, LineID, BaseTravelTime)
            key = (StationA, StationB, LineID)
            connections[key] = baseConnectionClass

    network.nodes = stations
    network.edges = connections


def processEvents(events, databaseFile, parameterObject, baseGraph, network):
    ATTENDANCE = parameterObject.ATTENDANCE
    TRAIN_PROPORTION = parameterObject.TRAIN_PROPORTION
    arrivalWindowMinutes = parameterObject.arrivalWindowMinutes
    departureWindowMinutes = parameterObject.departureWindowMinutes
    arrivalMinutesOffset = parameterObject.arrivalMinutesOffset
    departureMinutesOffset = parameterObject.departureMinutesOffset
    SIGMA_FACTOR = parameterObject.SIGMA_FACTOR
    MINIMUM_PEOPLE = parameterObject.MINIMUM_PEOPLE
    PROPEGATION_FACTOR = parameterObject.PROPAGATION_FACTOR

    for event in events.keys():
        venue = event[0]
        timings = events[event]
        startDifferenceMinutes = timings[1]
        endDifferenceMinutes = timings[2]
        stationsWithDistances = returnStationsWithDistances()
        capacity = findCapacity(databaseFile, venue)
        baseNumberOfPeopleAtStations = findBaseNumberOfPeople(
            capacity,
            ATTENDANCE,
            TRAIN_PROPORTION,
            startDifferenceMinutes,
            endDifferenceMinutes,
            arrivalWindowMinutes,
            departureWindowMinutes,
            arrivalMinutesOffset,
            departureMinutesOffset,
            stationsWithDistances,
            SIGMA_FACTOR
        )
        for station in baseNumberOfPeopleAtStations.keys():
            arrivals = baseNumberOfPeopleAtStations[station][0]
            departures = baseNumberOfPeopleAtStations[station][1]
            people = max(arrivals, departures)
            if people >= MINIMUM_PEOPLE:
                propegation(baseGraph, station, people, MINIMUM_PEOPLE, network, event, PROPEGATION_FACTOR)





def crowding(username, databaseFile):
    engine = create_engine("sqlite:///test.db")
    Session = sessionmaker(bind=engine)
    session = Session()

    stations = {}
    connections = {}

    parameterObject = getParameters(username, databaseFile)
    baseGraph = MakeGraph(databaseFile)
    network = classes.Network()

    createConnection(baseGraph, session, stations, connections, network) #Creates NotAffectedStation and NotAffectedConnection objects which are then stored in the dictionaries which are then stored in the network object
    baseInputData = takeInput()
    midTimeObject = calculateDefaultMidjourneyTime(baseInputData, databaseFile, parameterObject.CHANGING_TIME)
    events = findEventsInTimeFrame(midTimeObject, databaseFile, baseInputData, parameterObject.MAX_TIME_WINDOW, parameterObject.arrivalPeakOffset, parameterObject.departurePeakOffset)
    processEvents(events, databaseFile, parameterObject, baseGraph, network)

    #Gonna split into functions so won't need all of this but will just pass in the object and then extract data from there
