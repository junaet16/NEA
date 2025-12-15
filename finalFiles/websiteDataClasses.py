import sqlite3


class mainPagePathClass():
    def __init__(self, LineID):
        self.LineID = LineID
        self.ListOfStations = []
        self.LineName = None
        self.ListOfStationNames = []
        self.ListOfStationNamesAndDescriptions = []

    def addStation(self, Station):
        self.ListOfStations.append(Station)

    def getLineName(self, databaseFile):
        connection = sqlite3.connect(databaseFile)
        cursor = connection.cursor()

        cursor.execute("""
            SELECT LineName
            FROM Lines
            WHERE LineID = ?
            """, (self.LineID,))

        LineName = cursor.fetchall()[0][0]

        connection.close()

        self.LineName = LineName

    def getStationNames(self, databaseFile):
        connection = sqlite3.connect(databaseFile)
        cursor = connection.cursor()

        for i, NaPTAN in enumerate(self.ListOfStations):
            cursor.execute("""
                SELECT StationName
                FROM Stations
                WHERE NaPTAN = ?
                """, (NaPTAN,))
            result = cursor.fetchall()[0][0]

            self.ListOfStationNames.append([result, NaPTAN])

        connection.close()

    def getDescription(self, descriptionList):
        descriptionDictionary = {station[0]: station[1] for station in descriptionList}
        for stationData in self.ListOfStationNames:
            description = descriptionDictionary[stationData[1]]
            data = [stationData[0], stationData[1], description]
            self.ListOfStationNamesAndDescriptions.append(data)