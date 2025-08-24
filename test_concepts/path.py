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


def Make_Graph():
    connection = sqlite3.connect("nea.db")
    cursor = connection.cursor()
    listOfNeighbours = {}
    rows = cursor.execute("SELECT station_a, station_b, travel_time, line_id FROM connections").fetchall()
    for station_a, station_b, travel_time, line_id in rows:
        if station_a not in listOfNeighbours:
            listOfNeighbours[station_a] = []
        if [station_b, travel_time, line_id] not in listOfNeighbours[station_a]:
            listOfNeighbours[station_a].append([station_b, travel_time, line_id])
    connection.close()
    return listOfNeighbours

if __name__ == "__main__":
    listOfNeighbours = Make_Graph()
    print(listOfNeighbours)
    print("done")