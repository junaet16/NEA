import heapq
import sqlite3
import requests
import math
import collections

API_KEY = "0ff5a2076cd640cb957e63d6947efc61"
LINE_NAMES = [
    "bakerloo",
    "central",
    "circle",
    "district",
    "hammersmith-city",
    "jubilee",
    "metropolitan",
    "northern",
    "piccadilly",
    "victoria",
    "waterloo-city",
    "dlr",
    "elizabeth",
    "liberty",
    "lioness",
    "mildmay",
    "windrush",
    "weaver",
    "suffragette"
    ]
TRAVEL_TIME_DEFAULT = 3
TIME_PENALTY_DEFAULT = 5



def Make_Graph():
    connection = sqlite3.connect("nea.db")
    cursor = connection.cursor()
    listOfNeighbours = {}
    rows = cursor.execute("SELECT station_a, station_b, travel_time, line_id FROM connections").fetchall()
    for station_a, station_b, travel_time, line_id in rows:
        if station_a not in listOfNeighbours:
            listOfNeighbours[station_a] = []
        if [station_b, travel_time, line_id] not in listOfNeighbours[station_a]:
            listOfNeighbours[station_a].append([station_b, travel_time, line_id])
    connection.close()
    return listOfNeighbours


def Dijkstra_With_Penalty(listOfNeighbours, start, goal):
    distances = collections.defaultdict(lambda: math.inf)
    previous = {}
    visited = set()
    startState = (start, None)
    distances[startState] = 0
    minHeap = [(0, startState)]
    goalState = None

    while minHeap:
        currentCost, (currentStationID, currentLine) = heapq.heappop(minHeap)
        if (currentStationID, currentLine) in visited:
            continue
        else:
            visited.add((currentStationID, currentLine))

        if currentStationID == goal:
            goalState = (currentStationID, currentLine)
            break

        for nextStationID, nextTime, nextLine in listOfNeighbours[currentStationID]:
            if currentLine is not None and currentLine != nextLine:
                nextTime += TIME_PENALTY_DEFAULT

            newCost = currentCost + nextTime
            neighbourState = (nextStationID, nextLine)

            if newCost < distances[neighbourState]:
                distances[neighbourState] = newCost
                previous[neighbourState] = (currentStationID, currentLine, nextLine)
                heapq.heappush(minHeap, (newCost, neighbourState))

    steps = []
    stationPath = []

    currentState = goalState
    stationPath.append(currentState[0])

    while currentState != startState:
        previousStationID, previousLineID, lineUsed = previous[currentState]
        currentStationID, currentLineID = currentState
        steps.append((previousStationID, currentStationID, lineUsed, distances[(currentStationID, currentLineID)]))
        stationPath.append(previousStationID)
        currentState = (previousStationID, previousLineID)

    steps.reverse()
    stationPath.reverse()

    print(steps)
    print(stationPath)

    return stationPath, steps



if __name__ == "__main__":
    listOfNeighbours = Make_Graph()
    stationPath, steps = Dijkstra_With_Penalty(listOfNeighbours, "940GZZLULYS", "HUBEAL")
    print("done")