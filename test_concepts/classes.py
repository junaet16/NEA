#Class to create a Station
#Used when calling the TfL API to create stations whos data will then be stored in the database
#This is the parent class of the DikstraStation
class Station:
    def __init__(self, data):
        self.NaPTAN = data['id']
        self.StationName = data['name']
        self.Latitude = data['lat']
        self.Longitude = data['lon']
        self.TravelZone = "PLACEHOLDER"
        try:
            self.zone = data["zone"]
        except:
            self.zone = "PLACEHOLDER"  # I'll probably need to make another table of exceptions because TfL is annoying and I need to manually write the zones in a database


#Class to create a Line
#Would serve as more of a parent class than anything
class Line:
    def __init__(self, LineID, LineName, LineColour, AverageSpeed):
        self.LineID = LineID
        self.LineName = LineName
        self.LineColour = LineColour
        self.AverageSpeed = AverageSpeed


#This object will store data regarding any station affected by any events
class DijkstraStation(Station):
    def __init__(self, data):
        super().__init__(data)
        self.listOfEvents = []
