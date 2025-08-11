import sqlite3
import requests

API_KEY = "0ff5a2076cd640cb957e63d6947efc61"
LINE_NAMES = [
    "bakerloo",
    "central",
    "circle",
    "district",
    "hammersmith-city",
    "jubilee",
    "metropolitan",
    "northern",
    "piccadilly",
    "victoria",
    "waterloo-city",
    "dlr",
    "elizabeth",
    "liberty",
    "lioness",
    "mildmay",
    "windrush",
    "weaver",
    "suffragette"
    ]
TRAVEL_TIME_DEFAULT = 3

def create_tables():
    connection = sqlite3.connect("nea.db")
    cursor = connection.cursor()

    cursor.executescript("""
CREATE TABLE IF NOT EXISTS stations (
    station_id TEXT PRIMARY KEY,
    station_name TEXT,
    lat REAL,
    lon REAL,
    travel_zone INTEGER
);

CREATE TABLE IF NOT EXISTS lines (
    line_id TEXT PRIMARY KEY,
    line_name TEXT
);

CREATE TABLE IF NOT EXISTS connections (
    station_a TEXT,
    station_b TEXT,
    travel_time REAL,
    line_id TEXT,
    PRIMARY KEY (station_a, station_b, line_id)
);
""")

    connection.commit()
    connection.close()


class Station:
    def __init__(self, data):
        self.id = data["id"]
        self.name = data["name"]
        self.latitude = data["lat"]
        self.longitude = data["lon"]
        self.lines = []
        for line in data["lines"]:
            if line["id"] in LINE_NAMES:
                self.lines.append(line["id"])
        try:
            self.zone = data["zone"]
        except:
            self.zone = "PLACEHOLDER" #I'll probabbly need to make another table of exceptions because TfL is annoying and I need to manually write the zones in a databse
        #self.data = data


class Line:
    def __init__(self, name, branches):
        self.name = name
        self.branches = branches


def fetch_stations():
    stationDictionary = {}
    params = {
        "app_key": API_KEY,
    }
    for line in LINE_NAMES:
        url = f"https://api.tfl.gov.uk/Line/{line}/Route/Sequence/inbound"
        response = requests.get(url, params=params)
        data = response.json()
        stations = data["stations"]
        for station in stations:
            if station["id"] not in stationDictionary:
                stationDictionary[station["id"]] = Station(station)
    return stationDictionary


def fetch_lines(stationDictionary):
    linesDictionary = {}
    weirdStations = {}
    params = {
        "app_key": API_KEY,
    }
    for line in LINE_NAMES:
        url = f"https://api.tfl.gov.uk/Line/{line}/Route/Sequence/inbound"
        response = requests.get(url, params=params)
        data = response.json()
        branches = data["orderedLineRoutes"]
        listOflistsOfNAPTAN = []
        for fullBranch in branches:
            branch = fullBranch["naptanIds"]
            for i, id in enumerate(branch):
                if id not in stationDictionary:
                    if id not in weirdStations:
                        newURL = f"https://api.tfl.gov.uk/StopPoint/{id}"
                        newResponse = requests.get(newURL, params=params)
                        newData = newResponse.json()
                        newId = newData["hubNaptanCode"]
                        weirdStations[id] = newId
                    id = weirdStations[id]
                    branch[i] = id
            listOflistsOfNAPTAN.append(branch)
        linesDictionary[line] = Line(line, listOflistsOfNAPTAN)
    return  linesDictionary


def Save_TfL_Data(stationDictionary, linesDictionary):
    connection = sqlite3.connect("nea.db")
    cursor = connection.cursor()

    for line in linesDictionary.values():
        cursor.execute("INSERT INTO lines (line_id, line_name) VALUES (?, ?)", (line.name, line.name))

    for station in stationDictionary.values():
        cursor.execute("""
        INSERT INTO stations (station_id, station_name, lat, lon, travel_zone)
        VALUES (?, ?, ?, ?, ?)
        """, (station.id, station.name, station.latitude, station.longitude, station.zone))

    for line in linesDictionary.values():
        for branch in line.branches:
            for i in range(len(branch) - 1):
                try:
                    station_a = branch[i]
                    station_b = branch[i + 1]

                    cursor.execute("""
                    INSERT INTO connections (station_a, station_b, travel_time, line_id)
                    VALUES (?, ?, ?, ?)
                    """, (station_a, station_b, TRAVEL_TIME_DEFAULT, line.name))

                    cursor.execute("""
                    INSERT INTO connections (station_a, station_b, travel_time, line_id)
                    VALUES (?, ?, ?, ?)
                    """, (station_b, station_a, TRAVEL_TIME_DEFAULT, line.name))
                except:
                    pass
    connection.commit()
    connection.close()


def Make_Graph():
    connection = sqlite3.connect("nea.db")
    cursor = connection.cursor()
    listOfNeighbours = {}
    rows = cursor.execute("SELECT station_a, station_b, travel_time FROM connections").fetchall()
    for station_a, station_b, travel_time in rows:
        if station_a not in listOfNeighbours:
            listOfNeighbours[station_a] = []
        if [station_b, travel_time] not in listOfNeighbours[station_a]:
            listOfNeighbours[station_a].append([station_b, travel_time])
    connection.close()
    return listOfNeighbours


if __name__ == "__main__":
    #create_tables()
    #stationDictionary = fetch_stations()
    #linesDictionary = fetch_lines(stationDictionary)
    #Save_TfL_Data(stationDictionary, linesDictionary)
    listOfNeighbours = Make_Graph()
    print(listOfNeighbours)
    print("done")