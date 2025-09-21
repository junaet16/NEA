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


class Line:
    def __init__(self, LineID, LineName, LineColour, AverageSpeed):
        self.LineID = LineID
        self.LineName = LineName
        self.LineColour = LineColour
        self.AverageSpeed = AverageSpeed


class DijkstraStation(Station):
    def __init__(self, data):
        super().__init__(data)