import crowdingAlgorithm
import copy
import pathFinding
import customFunctions
import classes


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


def getAffectedOldPath(oldPath, affectedNetwork):
    affectedOldPath = []
    for station in oldPath:
        key = (station[0], station[1], station[2])
        connection = affectedNetwork.edges[key]
        newTime = station[3] * connection.LineDelay
        newData = (station[0], station[1], station[2], newTime)
        affectedOldPath.append(newData)

    return affectedOldPath


def main(date, journeyStart, startStation, endStation, databaseFile, username):
    affectedNetwork = crowdingAlgorithm.main(date, journeyStart, startStation, endStation, databaseFile, username)
    parameters = customFunctions.getParameters(username, databaseFile)

    baseGraph = pathFinding.MakeGraph(databaseFile)
    affectedGraph = GetaffectedGraph(baseGraph, affectedNetwork)
    print(baseGraph)
    print(affectedGraph)

    oldPath = pathFinding.Dijkstra(baseGraph, startStation, endStation, parameters.CHANGING_TIME)
    affectedOldPath = getAffectedOldPath(oldPath, affectedNetwork)
    newPath = pathFinding.Dijkstra(affectedGraph, startStation, endStation, parameters.CHANGING_TIME)

    affectedOldPathDesriptionObject = classes.Severity(affectedOldPath, username, databaseFile, startStation, affectedNetwork)
    affectedOldPathDesriptionObject.calculate()
    affectedOldPathDesriptions = affectedOldPathDesriptionObject.descriptions

    newPathDesptionObject = classes.Severity(newPath, username, databaseFile, startStation, affectedNetwork)
    newPathDesptionObject.calculate()
    newPathDescriptions = newPathDesptionObject.descriptions

    resultsObject = classes.Results(oldPath, newPath, affectedOldPath, newPathDescriptions, affectedOldPathDesriptions)

    print(resultsObject.oldPath)
    print(resultsObject.newPath)
    print(resultsObject.affectedOldPath)
    print(resultsObject.newPathDescriptions)
    print(resultsObject.affectedOldPathDesriptions)



if __name__ == '__main__':
    date = "03/12/2025"
    journeyStart = "18:30"
    startStation = "940GZZLULYS"
    endStation = "HUBSRA"
    databaseFile = "final.db"
    username = "Junaet"
    main(date, journeyStart, startStation, endStation, databaseFile, username)