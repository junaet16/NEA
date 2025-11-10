from abc import ABC, abstractmethod


class TransportClass(ABC):
    def __init__(self):
        self.currentPassengerLoad = 0
        self.DelayFactor = 1

    @abstractmethod
    def IsAffected(self):
        pass


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


class Parameters():
    def __init__(
            self,
            CHANGING_TIME,
            MAX_TIME_WINDOW,
            rawArrivalPeakOffset,
            rawDeparturePeakOffset,
            ATTENDANCE,
            TRAIN_PROPORTION,
            SIGMA_FACTOR,
            MINIMUM_PEOPLE,
            PERSON_DELAY,
            PROPAGATION_FACTOR
    ):
        self.CHANGING_TIME = CHANGING_TIME
        self.MAX_TIME_WINDOW = MAX_TIME_WINDOW
        self.rawArrivalPeakOffset = rawArrivalPeakOffset
        self.rawDeparturePeakOffset = rawDeparturePeakOffset
        self.ATTENDANCE = ATTENDANCE
        self.TRAIN_PROPORTION = TRAIN_PROPORTION
        self.SIGMA_FACTOR = SIGMA_FACTOR
        self.MINIMUM_PEOPLE = MINIMUM_PEOPLE
        self.PERSON_DELAY = PERSON_DELAY
        self.PROPAGATION_FACTOR = PROPAGATION_FACTOR

        self.arrivalWindowMinutes = None
        self.departureWindowMinutes = None
        self.arrivalPeakOffset = None
        self.departurePeakOffset = None
        self.arrivalMinutesOffset = None
        self.departureMinutesOffset = None

    def calculateWindow(self):
        self.arrivalWindowMinutes = self.MAX_TIME_WINDOW
        self.departureWindowMinutes = self.MAX_TIME_WINDOW

    def calculatePeakOffset(self):
        import datetime
        self.arrivalPeakOffset = datetime.timedelta(minutes=15)
        self.departurePeakOffset = datetime.timedelta(minutes=15)

    def calculateMinutesOffset(self):
        self.arrivalMinutesOffset = self.arrivalPeakOffset.total_seconds() / 60
        self.departureMinutesOffset = self.departurePeakOffset.total_seconds() / 60


class Fixture():
    def __init__(self, league, home, away, time):
        self.league = league
        self.home = home
        self.away = away
        self.time = time


#Date object contains the date and a list of fixture objects
#Date object's findRelevantFixtures method deletes all fixtures not in London
class Date():
    def __init__(self, date, fixtures):
        self.date = date
        self.fixtures = fixtures

    def findRelevantFixtures(self):
        relevantFixtures = []
        for fixture in self.fixtures:
            home = fixture.home
            London = False
            #Check if home is in London - NEED to do
            if London:
                relevantFixtures.append(fixture)
        self.fixtures = relevantFixtures


#Contains a list of date objects
class AllDates():
    def __init__(self, dates):
        self.dates = dates

    def findRelevantDates(self):
        relevantDates = []
        for dateObject in self.dates:
            dateObject.findRelevantFixtures() #Filters out all non-relevant
            if len(dateObject.fixtures) > 0:
                relevantDates.append(dateObject) #This means at least one event on this date is in London

    def storeInDatabase(self):
        pass #Finish
    

class Line():
    def __init__(self, connectionObjects, lineID):
        self.connections = connectionObjects
        self.numberOfConnections = 0
        self.TotalDelay = 0
        self.AverageDelay = 0
        
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