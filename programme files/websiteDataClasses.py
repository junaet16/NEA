import sqlite3


# This class is used to format a path segment for display on the main page.
# Each instance represents a continuous segment of a journey on a single line,
# containing the stations travelled through on that line along with crowding descriptions.
class mainPagePathClass():
    def __init__(self, LineID):
        self.LineID = LineID # The internal LineID used in the database
        self.ListOfStations = [] # List of station NaPTANs in the order they are visited on this line
        self.LineName = None # Human-readable line name (e.g. "Central Line")
        self.ListOfStationNames = [] # List of [StationName, NaPTAN]
        self.ListOfStationNamesAndDescriptions = [] # Final display format including crowding description

    # Adds a station (identified by NaPTAN) to the list of stations for this line segment
    def addStation(self, Station):
        self.ListOfStations.append(Station)

    # Fetches the human-readable name of the line from the database and stores it in the LineName attribute
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

    # Converts the stored list of station NaPTANs into human-readable station names while preserving the NaPTAN for later lookups (e.g. crowding descriptions)
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

            # Stored as [StationName, NaPTAN] so both display and lookup are possible
            self.ListOfStationNames.append([result, NaPTAN])

        connection.close()

    # Matches each station in this path segment with its crowding description
    # descriptionList format: [[NaPTAN, Description], ...]
    # Final format stored as: [StationName, NaPTAN, Description]
    def getDescription(self, descriptionList):
        # Convert list into dictionary for fast lookup by NaPTAN
        descriptionDictionary = {station[0]: station[1] for station in descriptionList}

        for stationData in self.ListOfStationNames:
            description = descriptionDictionary[stationData[1]]
            data = [stationData[0], stationData[1], description]
            self.ListOfStationNamesAndDescriptions.append(data)