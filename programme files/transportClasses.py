from abc import ABC, abstractmethod



# Abstract base class for all transport-related components
# Holds common attributes used for crowding and delay simulation
class TransportClass(ABC):
    def __init__(self):
        self.currentPassengerLoad = 0 #initially set to 0 and is the extra number of people present due to the events
        self.DelayFactor = 1 # initially set to 1 and is the factor by which the time to travel would be multiplied by to simulate crowding


    @abstractmethod
    def IsAffected(self):
        pass



# Represents a transport line consisting of multiple connections
# Responsible for spreading delay across all connections on the line
class Line():
    def __init__(self, connectionObjects, lineID):
        self.connections = connectionObjects
        self.numberOfConnections = 0
        self.TotalDelay = 0
        self.AverageDelay = 0
        self.lineID = lineID


    # Counts how many connections exist on this line
    def calculateTotalNumberOfConnections(self):
        self.numberOfConnections = len(self.connections)


    # Calculates the total delay factor across all connections
    def calculateTotalDelay(self):
        totalDelay = 0
        for connection in self.connections:
            totalDelay += connection.DelayFactor
        self.TotalDelay = totalDelay


    # Computes the average delay factor for the line
    def calculateAverageDelay(self):
        averageDelay = self.TotalDelay / self.numberOfConnections
        self.AverageDelay = averageDelay


    # Applies the average delay back onto each connection
    def spreadDelay(self):
        for connection in self.connections:
            connection.LineDelay = self.AverageDelay


    # Performs all line-level delay calculations in sequence
    def doAllCalculations(self):
        self.calculateTotalNumberOfConnections()
        self.calculateTotalDelay()
        self.calculateAverageDelay()
        self.spreadDelay()


# Base class for all station types
class Station(TransportClass):
    def __init__(self, NaPTAN, StationName):
        super().__init__()
        self.NaPTAN = NaPTAN
        self.StationName = StationName


    def IsAffected(self):
        pass #IsAffected() is intentionally deferred to concrete subclasses - AffectedDijkstraStation returns True, NotAffectedDijkstraStation returns False



# Station class used during database creation
# Includes geographic coordinates
class CreationStation(Station):
    def __init__(self, NaPTAN, StationName, Latitude, Longitude):
        super().__init__(NaPTAN, StationName)
        self.Latitude = Latitude
        self.Longitude = Longitude


    def IsAffected(self):
        pass



#Serves as the parent class of the affected and not affected dijkstra station classes
class DijkstraStation(Station):
    def __init__(self, NaPTAN, StationName):
        super().__init__(NaPTAN, StationName)


    def IsAffected(self):
        pass #IsAffected() is intentionally deferred to concrete subclasses - AffectedDijkstraStation returns True, NotAffectedDijkstraStation returns False



# Represents a station affected by nearby events
class AffectedDijkstraStation(DijkstraStation):
    def __init__(self, NaPTAN, StationName):
        super().__init__(NaPTAN, StationName)
        self.events = {} #{(VenueName, Date) : NumberOfPeople}


    def IsAffected(self):
        return True


    # Calculates the total passenger load caused by all events
    def calculatePassengerLoad(self):
        for event in self.events.keys():
            numberOfPeople = self.events[event]
            self.currentPassengerLoad += numberOfPeople
        return self.currentPassengerLoad


    # Calculates the station delay factor based on passenger load
    def calculateDelay(self, PERSON_DELAY):
        extraDelay = PERSON_DELAY * self.currentPassengerLoad
        self.DelayFactor += extraDelay



# Represents a station not affected by any events
class NotAffectedDijkstraStation(DijkstraStation):
    def __init__(self, NaPTAN, StationName):
        super().__init__(NaPTAN, StationName)


    def IsAffected(self):
        return False



# Parent class for all connection types used in Dijkstra's algorithm
class Connection(TransportClass):
    def __init__(self, StationA, StationB, LineID, BaseTravelTime):
        super().__init__()
        self.StationA = StationA
        self.StationB = StationB
        self.LineID = LineID
        self.connectionReference = (self.StationA, self.StationB, self.LineID) #Unique identifier
        self.BaseTravelTime = BaseTravelTime
        self.LineDelay = 0


    @abstractmethod
    def IsAffected(self):
        pass


    @abstractmethod
    def returnDelay(self):
        pass



# Connection that is not affected by events or crowding
class NotAffectedConnection(Connection):
    def __init__(self, StationA, StationB, LineID, BaseTravelTime):
        super().__init__(StationA, StationB, LineID, BaseTravelTime)


    def IsAffected(self):
        return False


    def returnDelay(self): #Because it isn't affected
        self.DelayFactor = 1
        return 1



# Connection affected by delays at one or both stations
class AffectedConnection(Connection):
    def __init__(self, StationA, StationB, LineID, BaseTravelTime, StationADelayFactor, StationBDelayFactor):
        super().__init__(StationA, StationB, LineID, BaseTravelTime)
        self.StationADelayFactor = StationADelayFactor
        self.StationBDelayFactor = StationBDelayFactor


    def IsAffected(self):
        return True


    # Calculates delay as the average of both station delay factors -- use of polymorphism as the two connection types are handled differently
    def returnDelay(self):
        averageDelayFactor = (self.StationADelayFactor + self.StationBDelayFactor) / 2
        self.DelayFactor = averageDelayFactor
        return averageDelayFactor



# Massive container for all the data for me about the graph
class Network():
    def __init__(self):
        self.nodes = {} #Dictionary of station objects with the key being the NaPTAN
        self.edges = {} #Dictionary of connection objects with the key being (StationA, StationB, LineID)
        self.SpreadOutEdges = {} #Used in an earlier version of the delay spreading algorithm - retained in case it is needed again in the future