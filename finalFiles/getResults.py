import crowdingAlgorithm
import copy
import pathFinding
import customFunctions
import classes
import sqlite3


def getNaPTAN(name, database):
    connection = sqlite3.connect(database)
    cursor = connection.cursor()

    cursor.execute(f"""
        SELECT NaPTAN
        FROM Stations
        WHERE StationName = ?""", (name,))
    result = cursor.fetchall()[0][0]
    return result


def GetaffectedGraph(baseGraph, affectedNetwork):
    affectedGraph = copy.deepcopy(baseGraph)

    for StationA in affectedGraph.keys():
        connectedStations = affectedGraph[StationA]
        for connection in connectedStations:
            StationB = connection[0]
            LineID = connection[2]
            key = (StationA, StationB, LineID)
            LineDelay = affectedNetwork.edges[key].LineDelay
            oldTime = connection[1]
            newTime = oldTime * LineDelay
            connection[1] = newTime

    return affectedGraph


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
            if connectedStationB == StationB and connectedLineID == LineID:
                strippedGraph[StationA] = [connectedStation]

    return strippedGraph


def getAffectedOldPath(oldPath, affectedGraph, startStation, endStation, CHANGING_TIME):
    strippedGraph = getStrippedGraph(oldPath, affectedGraph)
    returnPath = pathFinding.Dijkstra(strippedGraph, startStation, endStation, CHANGING_TIME)

    return returnPath


def main(date, journeyStart, startStationName, endStationName, databaseFile, username):
    startStation = getNaPTAN(startStationName, databaseFile)
    endStation = getNaPTAN(endStationName, databaseFile)

    affectedNetwork = crowdingAlgorithm.main(date, journeyStart, startStation, endStation, databaseFile, username)
    parameters = customFunctions.getParameters(username, databaseFile)

    baseGraph = pathFinding.MakeGraph(databaseFile)
    affectedGraph = GetaffectedGraph(baseGraph, affectedNetwork)

    oldPath = pathFinding.Dijkstra(baseGraph, startStation, endStation, parameters.CHANGING_TIME)
    affectedOldPath = getAffectedOldPath(oldPath, affectedGraph, startStation, endStation, parameters.CHANGING_TIME)
    newPath = pathFinding.Dijkstra(affectedGraph, startStation, endStation, parameters.CHANGING_TIME)

    affectedOldPathDesriptionObject = classes.Severity(affectedOldPath, username, databaseFile, startStation, affectedNetwork)
    affectedOldPathDesriptionObject.calculate()
    affectedOldPathDesriptions = affectedOldPathDesriptionObject.descriptions

    newPathDesptionObject = classes.Severity(newPath, username, databaseFile, startStation, affectedNetwork)
    newPathDesptionObject.calculate()
    newPathDescriptions = newPathDesptionObject.descriptions

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