import sqlite3


class Severity():
    def __init__(self, originalPath, username, databaseFile, start, affectedNetwork):
        self.descriptions = []
        self.originalPath = originalPath
        self.username = username
        self.databaseFile = databaseFile
        self.start = start
        self.affectedNetwork = affectedNetwork
        self.normal = 0
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
        self.normal, self.slightly, self.busy = results


    def getDescription(self, factor):
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
        firstFactor = self.affectedNetwork.nodes[station].DelayFactor
        firstDescription = self.getDescription(firstFactor)
        self.descriptions.append([station, firstDescription])


    def makePath(self):
        self.addDescription(self.start)
        for connectionData in self.originalPath:
            station = connectionData[1]
            self.addDescription(station)


    def calculate(self):
        self.getParameters()
        self.makePath()


class Results():
    def __init__(self, oldPath, newPath, affectedOldPath, newPathDescriptions, affectedOldPathDesriptions):
        self.oldPath = oldPath
        self.newPath = newPath
        self.affectedOldPath = affectedOldPath
        self.newPathDescriptions = newPathDescriptions
        self.affectedOldPathDesriptions = affectedOldPathDesriptions