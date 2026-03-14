import sqlite3



# Container and to call class methods
class Severity():
    def __init__(self, originalPath, username, databaseFile, start, affectedNetwork):
        self.descriptions = [] # Stores descriptions for each station along the path, e.g., [["StationA", "Normal"], ["StationB", "Busy"]]
        self.originalPath = originalPath # The path returned by Dijkstra [(prevStation, currStation, line, cost), ...]
        self.username = username # Username to fetch user-specific thresholds for crowding
        self.databaseFile = databaseFile # Database file containing the thresholds
        self.start = start # Starting station for the path
        self.affectedNetwork = affectedNetwork # Network object (instance of Network class) containing station nodes with DelayFactor
        self.normal = 0 # Threshold values that will be fetched from the database
        self.slightly = 0
        self.busy = 0


    def getParameters(self):
        connection = sqlite3.connect(self.databaseFile)
        cursor = connection.cursor()

        cursor.execute("""
            SELECT NORMAL, SLIGHTLY, BUSY
            FROM Users
            WHERE Username = ?
            """, (self.username,))
        results = cursor.fetchall()[0]

        connection.close()

        self.normal, self.slightly, self.busy = results


    def getDescription(self, factor):
        # Map a DelayFactor to a human-readable description using thresholds
        if factor > self.busy:
            description = "Severe"
        elif factor > self.slightly:
            description = "Busy"
        elif factor > self.normal:
            description = "Slightly"
        else:
            description = "Normal"

        return description


    def addDescription(self, station):
        firstFactor = self.affectedNetwork.nodes[station].DelayFactor # Get the DelayFactor of the station from the network
        firstDescription = self.getDescription(firstFactor) # Convert factor to description
        self.descriptions.append([station, firstDescription]) # Append [station, description] to the list


    def makePath(self):
        self.addDescription(self.start) # Add the starting station first

        # Iterate over the original path returned by Dijkstra
        # path elements are (prevStation, currStation, lineUsed, cumulativeCost)
        for connectionData in self.originalPath:
            station = connectionData[1] # Current station in the path
            self.addDescription(station)


    def calculate(self):
        self.getParameters()
        self.makePath()



#Container for all the results
class Results():
    def __init__(self, oldPath, newPath, affectedOldPath, newPathDescriptions, affectedOldPathDesriptions):
        self.oldPath = oldPath # The original shortest path without considering delays
        self.newPath = newPath # The new path that may be optimised to avoid delays
        self.affectedOldPath = affectedOldPath # The original path but with delays applied (affected)
        self.newPathDescriptions = newPathDescriptions # Descriptions of crowding for the new path
        self.affectedOldPathDesriptions = affectedOldPathDesriptions # Descriptions of crowding for the affected old path