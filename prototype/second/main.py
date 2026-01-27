import testData
import pathFinding


if __name__ == '__main__':

    # Create the database
    databaseFile = "test.db"
    testData.CreateTestDatabase(databaseFile)

    # Make a graph in the form {StationA: [[StationB, travelTime, Line], ...], ...]}
    listOfNeighbourStations = pathFinding.MakeGraph(databaseFile)
    print(listOfNeighbourStations)

    # Example stations and CHANGING_TIME
    startStation = "A"
    endStation = "C"
    CHANGING_TIME = 4.4

    # The path in the form [(StationA, StationB, Line, timeToStation), ...]
    pathSteps = pathFinding.Dijkstra(listOfNeighbourStations, startStation, endStation, CHANGING_TIME)
    print(pathSteps)