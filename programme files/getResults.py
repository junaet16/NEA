import crowdingAlgorithm
import copy # Used for deep copying graphs so original data isn't altered
import pathFinding
import customFunctions
import classes
import sqlite3


# Fetch the NaPTAN (unique station code) from a station name
def getNaPTAN(name, database):
    connection = sqlite3.connect(database)
    cursor = connection.cursor()

    cursor.execute(f"""
        SELECT NaPTAN
        FROM Stations
        WHERE StationName = ?""", (name,))
    result = cursor.fetchall()[0][0]

    connection.close()

    return result


# Create a modified graph where each connection's travel time is multiplied by the delay factor
def GetaffectedGraph(baseGraph, affectedNetwork):
    # Deep copy to avoid modifying the original base graph
    affectedGraph = copy.deepcopy(baseGraph)

    for StationA in affectedGraph.keys():

        connectedStations = affectedGraph[StationA]

        for connection in connectedStations:

            StationB = connection[0]
            LineID = connection[2]
            key = (StationA, StationB, LineID)

            # Multiply old travel time by the LineDelay factor from the affected network
            LineDelay = affectedNetwork.edges[key].LineDelay
            oldTime = connection[1]
            newTime = oldTime * LineDelay
            connection[1] = newTime

    return affectedGraph


# Strip down the affected graph to only include the edges in the old path
# This is used to calculate delays along the original route
def getStrippedGraph(oldPath, affectedGraph):
    strippedGraph = {}

    for connection in oldPath:
        StationA = connection[0]
        StationB = connection[1]
        LineID = connection[2]

        connectedStations = affectedGraph[StationA]

        for connectedStation in connectedStations:
            connectedStationB = connectedStation[0]
            connectedLineID = connectedStation[2]

            # Only keep the edge if it matches the original path connection
            # Just adjusting the time of individual connections of the base path, doesn't change the time taken to change trains, which is a flaw fixed with this implementation
            if connectedStationB == StationB and connectedLineID == LineID:
                strippedGraph[StationA] = [connectedStation]

    return strippedGraph


# Compute the path using only the connections from the old path but considering updated travel times
def getAffectedOldPath(oldPath, affectedGraph, startStation, endStation, CHANGING_TIME):
    strippedGraph = getStrippedGraph(oldPath, affectedGraph)
    returnPath = pathFinding.Dijkstra(strippedGraph, startStation, endStation, CHANGING_TIME)

    return returnPath


# Main function for calling all the functions and calculating new paths and evaluating delays
def main(date, journeyStart, startStationName, endStationName, databaseFile, username):

    # Convert station names to NaPTAN codes
    startStation = getNaPTAN(startStationName, databaseFile)
    endStation = getNaPTAN(endStationName, databaseFile)

    # Generate the affected network (crowding and delays applied)
    affectedNetwork = crowdingAlgorithm.main(date, journeyStart, startStation, endStation, databaseFile, username)
    parameters = customFunctions.getParameters(username, databaseFile)

    # Create the base graph (unaffected network) and then apply delays to get the affected graph
    baseGraph = pathFinding.MakeGraph(databaseFile)
    affectedGraph = GetaffectedGraph(baseGraph, affectedNetwork)

    # Calculate paths
    oldPath = pathFinding.Dijkstra(baseGraph, startStation, endStation, parameters.CHANGING_TIME)
    affectedOldPath = getAffectedOldPath(oldPath, affectedGraph, startStation, endStation, parameters.CHANGING_TIME)
    newPath = pathFinding.Dijkstra(affectedGraph, startStation, endStation, parameters.CHANGING_TIME)

    # Create objects to store severity and description of delays on old vs affected old path
    affectedOldPathDesriptionObject = classes.Severity(affectedOldPath, username, databaseFile, startStation, affectedNetwork)
    affectedOldPathDesriptionObject.calculate()
    affectedOldPathDesriptions = affectedOldPathDesriptionObject.descriptions

    # Same for new path
    newPathDesptionObject = classes.Severity(newPath, username, databaseFile, startStation, affectedNetwork)
    newPathDesptionObject.calculate()
    newPathDescriptions = newPathDesptionObject.descriptions

    # Compile all paths and descriptions into a results object
    resultsObject = classes.Results(oldPath, newPath, affectedOldPath, newPathDescriptions, affectedOldPathDesriptions)
    return resultsObject


if __name__ == '__main__':
    date = "03/12/2025"
    journeyStart = "18:30"
    startStation = "Leytonstone Underground Station"
    endStation = "Stonebridge Park"
    databaseFile = "final.db"
    username = "Junaet"

    resultsObject = main(date, journeyStart, startStation, endStation, databaseFile, username)

    print(resultsObject.oldPath)
    print(resultsObject.newPath)
    print(resultsObject.affectedOldPath)
    print(resultsObject.newPathDescriptions)
    print(resultsObject.affectedOldPathDesriptions)