import testData
import pathFinding


if __name__ == '__main__':

    # Create the database
    databaseFile = "test.db"
    testData.CreateTestDatabase(databaseFile)

    # Make a graph in the form {StationA: [[StationB, travelTime, Line], ...], ...]}
    listOfNeighbourStations = pathFinding.MakeGraph(databaseFile)
    print(listOfNeighbourStations)

    # Example stations
    startStation = "A"
    endStation = "C"

    # The path in the form [(StationA, StationB, Line, timeToStation), ...]
    pathSteps = pathFinding.Dijkstra(listOfNeighbourStations, startStation, endStation)
    print(pathSteps)