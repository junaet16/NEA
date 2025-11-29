import crowdingAlgorithm
import copy
import pathFinding
import customFunctions
import classes


def GetaffectedGraph(baseGraph, affectedNetwork):
    affectedGraph = copy.deepcopy(baseGraph)

    for edgeKey in affectedNetwork.edges.keys():
        connection = affectedNetwork.edges[edgeKey]
        StationA = connection.StationA
        StationB = connection.StationB
        LineID = connection.LineID
        connectedStations = affectedGraph[StationB]

        for i, connectedStationData in enumerate(connectedStations):
            if connectedStationData[0] == StationB and connectedStationData[2] == LineID:
                oldTime = connectedStationData[1]
                newTime = oldTime * connection.DelayFactor
                connectedStationData[1] = newTime

    return affectedGraph


def getAffectedOldPath(oldPath, affectedNetwork):
    affectedOldPath = []
    for station in oldPath:
        key = (station[0], station[1], station[2])
        connection = affectedNetwork.edges[key]
        DelayFactor = connection.DelayFactor
        newTime = station[3] * DelayFactor
        newData = (station[0], station[1], station[2], newTime)
        affectedOldPath.append(newData)

    return affectedOldPath


def main(date, journeyStart, startStation, endStation, databaseFile, username):
    affectedNetwork = crowdingAlgorithm.main(date, journeyStart, startStation, endStation, databaseFile, username)
    parameters = customFunctions.getParameters(username, databaseFile)

    baseGraph = pathFinding.MakeGraph(databaseFile)
    affectedGraph = GetaffectedGraph(baseGraph, affectedNetwork)

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