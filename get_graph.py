import requests
import csv

#Global stuff
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
lines = {}
listOfStations = {}
weirdStations = {}


#Extract different data from data later (not important right now)
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
        self.data = data



#This class puts the different branches under each line
class Line:
    def __init__(self, name, branches):
        self.name = name
        self.branches = branches


#Makes a list of stations and their data and creates a Station class
def GetStation(API_KEY, LINE_NAMES):
    params = {
        "app_key": API_KEY,
    }
    for line in LINE_NAMES:
        url = f"https://api.tfl.gov.uk/Line/{line}/Route/Sequence/inbound"
        response = requests.get(url, params=params)
        data = response.json()
        stations = data["stations"]
        for station in stations:
            listOfStations[station["id"]] = Station(station)


#Get a list of lines
def GetLines():
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
                if id not in listOfStations:
                    if id not in weirdStations:
                        newURL = f"https://api.tfl.gov.uk/StopPoint/{id}"
                        newResponse = requests.get(newURL, params=params)
                        newData = newResponse.json()
                        newId = newData["hubNaptanCode"]
                        weirdStations[id] = newId
                    id = weirdStations[id]
                    branch[i] = id
            listOflistsOfNAPTAN.append(branch)
        lines[line] = Line(line, listOflistsOfNAPTAN)


#Creates a dictionary of Station IDs and the stations connected to them
def makeGraph():
    listOfNeighbours = {}
    for line in lines.values():
        for branch in line.branches:
            for i, id in enumerate(branch):
                if id not in listOfNeighbours:
                    neighbours = []
                else:
                    neighbours = listOfNeighbours[id]
                nextID = i + 1
                previousID = i - 1
                try:
                    if [branch[nextID], 3] not in neighbours:
                        neighbours.append([branch[nextID], 3])
                except:
                    pass
                if previousID >= 0 and [branch[previousID], 3] not in neighbours:
                    neighbours.append([branch[previousID], 3])
                listOfNeighbours[id] = neighbours
    print(listOfNeighbours)



if __name__ == "__main__":
    GetStation(API_KEY, LINE_NAMES)
    GetLines()
    #makeGraph()
    print("end")