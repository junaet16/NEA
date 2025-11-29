from abc import ABC, abstractmethod


class TransportClass(ABC):
    def __init__(self):
        self.currentPassengerLoad = 0
        self.DelayFactor = 1

    @abstractmethod
    def IsAffected(self):
        pass


class Line():
    def __init__(self, connectionObjects, lineID):
        self.connections = connectionObjects
        self.numberOfConnections = 0
        self.TotalDelay = 0
        self.AverageDelay = 0
        self.lineID = lineID

    def calculateTotalNumberOfConnections(self):
        self.numberOfConnections = len(self.connections)

    def calculateTotalDelay(self):
        totalDelay = 0
        for connection in self.connections:
            totalDelay += connection.DelayFactor
        self.TotalDelay = totalDelay

    def calculateAverageDelay(self):
        averageDelay = self.TotalDelay / self.numberOfConnections
        self.AverageDelay = averageDelay

    def spreadDelay(self):
        for connection in self.connections:
            connection.LineDelay = self.AverageDelay

    def doAllCalculations(self):
        self.calculateTotalNumberOfConnections()
        self.calculateTotalDelay()
        self.calculateAverageDelay()
        self.spreadDelay()


class Station(TransportClass):
    def __init__(self, NaPTAN, StationName):
        super().__init__()
        self.NaPTAN = NaPTAN
        self.StationName = StationName

    def IsAffected(self):
        pass


class CreationStation(Station):
    def __init__(self, NaPTAN, StationName, Latitude, Longitude):
        super().__init__(NaPTAN, StationName)
        self.Latitude = Latitude
        self.Longitude = Longitude

    def IsAffected(self):
        pass


class DijkstraStation(Station):
    def __init__(self, NaPTAN, StationName):
        super().__init__(NaPTAN, StationName)

    def IsAffected(self):
        pass


class AffectedDijkstraStation(DijkstraStation):
    def __init__(self, NaPTAN, StationName):
        super().__init__(NaPTAN, StationName)
        self.events = {} #{(VenueName, Date) : NumberOfPeople}

    def IsAffected(self):
        return True

    def calculatePassengerLoad(self):
        for event in self.events.keys():
            numberOfPeople = self.events[event]
            self.currentPassengerLoad += numberOfPeople
        return self.currentPassengerLoad

    def calculateDelay(self, PERSON_DELAY):
        extraDelay = PERSON_DELAY * self.currentPassengerLoad
        self.DelayFactor += extraDelay


class NotAffectedDijkstraStation(DijkstraStation):
    def __init__(self, NaPTAN, StationName):
        super().__init__(NaPTAN, StationName)

    def IsAffected(self):
        return False


#ParentClass of Dijkstra Connection
class Connection(TransportClass):
    def __init__(self, StationA, StationB, LineID, BaseTravelTime):
        super().__init__()
        self.StationA = StationA
        self.StationB = StationB
        self.LineID = LineID
        self.connectionReference = (self.StationA, self.StationB, self.LineID)
        self.BaseTravelTime = BaseTravelTime
        self.LineDelay = 0

    @abstractmethod
    def IsAffected(self):
        pass

    @abstractmethod
    def returnDelay(self):
        pass


class NotAffectedConnection(Connection):
    def __init__(self, StationA, StationB, LineID, BaseTravelTime):
        super().__init__(StationA, StationB, LineID, BaseTravelTime)

    def IsAffected(self):
        return False

    def returnDelay(self):
        self.DelayFactor = 1
        return 1


class AffectedConnection(Connection):
    def __init__(self, StationA, StationB, LineID, BaseTravelTime, StationADelayFactor, StationBDelayFactor):
        super().__init__(StationA, StationB, LineID, BaseTravelTime)
        self.StationADelayFactor = StationADelayFactor
        self.StationBDelayFactor = StationBDelayFactor

    def IsAffected(self):
        return True

    #Polymorphism?????
    def returnDelay(self):
        averageDelayFactor = (self.StationADelayFactor + self.StationBDelayFactor) / 2
        self.DelayFactor = averageDelayFactor
        return averageDelayFactor


class Network():
    def __init__(self):
        self.nodes = {}
        self.edges = {}
        self.SpreadOutEdges = {}