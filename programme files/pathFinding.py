import sqlite3
import collections
import math
import heapq


#Fetches all the unique connections from the database and for every StationA, it adds to a list all StationBs in their own list including Line and travel time
#Forms dictionary in the form {StationA : [[StationB, BaseTravelTime, LineID], [StationC, ...], ...]}
def MakeGraph(databaseFile):
    connection = sqlite3.connect(databaseFile)
    cursor = connection.cursor()
    listOfNeighbourStations = {} # {StationA: [[StationB, BaseTravelTime, LineID], ...]}
    rows = cursor.execute("SELECT StationA, StationB, LineID, BaseTravelTime FROM connections").fetchall()

    for StationA, StationB, LineID, BaseTravelTime in rows: #For every unique connection (direction matters)
        if StationA not in listOfNeighbourStations:
            listOfNeighbourStations[StationA] = []
        if [StationB, BaseTravelTime, LineID] not in listOfNeighbourStations[StationA]:
            listOfNeighbourStations[StationA].append([StationB, BaseTravelTime, LineID])

    connection.close()
    return listOfNeighbourStations


# It is assumed that all stations can be accessed from any other station because the graph is made from the data for me stored in the database which is always complete for the function to be called in the first place
#On the TfL network, every station is eventually connected to every other station
def Dijkstra(graph, startStation, goalStation, CHANGING_TIME, penalty=True):
    distances = collections.defaultdict(lambda: math.inf) #Best known time to each station
    cameFrom = {} #To reconstruct path later
    visited = set() #Stores visited stations

    # Start at the given station, with no line yet chosen
    startState = (startStation, None) # This is the state is key because the line change penalty depends on the previous line
    distances[startState] = 0

    frontier = [(0, startState)] #The first item is always the cheapest station to go to next
    goalState = None #Store the final when we reach the goal


    while frontier: #This condition means it runs until all the paths have been explored - till the last one
        currentCost, (currentStation, currentLine) = heapq.heappop(frontier) #Deletes the next route at the top so that the next one to be explored can be at the top

        # Skip if already fully explored this (station, line) - If at the top of the heap, then it means that it is the shortest ever path to the station, which means it is visited
        if (currentStation, currentLine) in visited:
            continue
        visited.add((currentStation, currentLine))

        # Stop if reached the goal station
        if currentStation == goalStation:
            goalState = (currentStation, currentLine)
            break

        # Explore all neighbours of this station
        for nextStation, baseTravelTime, nextLine in graph[currentStation]:
            travelTime = baseTravelTime

            if penalty: #Can be turned off if needed (for testing purposes)
                if currentLine is not None and currentLine != nextLine:
                #Initially no line is chosen, so the penalty is not added for changing lines
                #If the line is switched to travel to the next station, the penalty is added to the cost
                    travelTime += CHANGING_TIME

            # New total time to reach the neighbour
            newCost = currentCost + travelTime
            neighbourState = (nextStation, nextLine)

            # Only update if we found a faster way
            if newCost < distances[neighbourState]:
                distances[neighbourState] = newCost
                cameFrom[neighbourState] = (currentStation, currentLine, nextLine)
                heapq.heappush(frontier, (newCost, neighbourState))

    # Start from the goal and trace back to the start
    pathSteps = []
    currentState = goalState

    while currentState != startState:
        prevStation, prevLine, lineUsed = cameFrom[currentState]
        currStation, currLine = currentState
        pathSteps.append((prevStation, currStation, lineUsed, distances[(currStation, currLine)]))
        currentState = (prevStation, prevLine)


    pathSteps.reverse()
    return pathSteps