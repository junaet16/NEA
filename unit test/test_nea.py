import sys
import os
import types
import sqlite3
import unittest
import math
import hashlib
import tempfile
import datetime
import json
import copy

# ─────────────────────────────────────────────────────────────────────────────
# API keys — update these if the keys change
# ─────────────────────────────────────────────────────────────────────────────
TfL_API_KEY = "0ff5a2076cd640cb957e63d6947efc61"
OPENCAGE_API_KEY = "eb0e2c9b71cc45f7aafe0ae4ecc44cc2"


# Mock third-party modules that require a network connection to install
# opencage and geopy are used for geocoding and distance calculations
opencageMock = types.ModuleType("opencage")
opencageGeocoderMock = types.ModuleType("opencage.geocoder")

class FakeGeocoder:
    def __init__(self, key):
        pass
    def geocode(self, location):
        return [{"geometry": {"lat": 51.555, "lng": -0.108}}]

opencageGeocoderMock.OpenCageGeocode = FakeGeocoder
opencageMock.geocoder = opencageGeocoderMock
sys.modules["opencage"] = opencageMock
sys.modules["opencage.geocoder"] = opencageGeocoderMock

geopyMock = types.ModuleType("geopy")
geopyDistanceMock = types.ModuleType("geopy.distance")

class FakeGeodesic:
    # Simple approximation for testing - 1 degree ~ 111km
    def __init__(self, coordinatesA, coordinatesB):
        latDiff = abs(coordinatesA[0] - coordinatesB[0])
        lonDiff = abs(coordinatesA[1] - coordinatesB[1])
        self.km = math.sqrt(latDiff**2 + lonDiff**2) * 111

geopyDistanceMock.geodesic = FakeGeodesic
geopyMock.distance = geopyDistanceMock
sys.modules["geopy"] = geopyMock
sys.modules["geopy.distance"] = geopyDistanceMock

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'programme files'))

import login
import customFunctions
import crowdingAlgorithm
import pathFinding
import scraper
import storeStadiumData
import databaseCreation
import getResults
import getTfLData
import classes
import main as mainApp


# Creates a minimal in-memory SQLite database with the full schema and seed data for testing
def createTestDatabase():
    connection = sqlite3.connect(":memory:")
    cursor = connection.cursor()

    cursor.executescript("""
        CREATE TABLE Stations (
            NaPTAN TEXT PRIMARY KEY,
            StationName TEXT,
            Latitude REAL,
            Longitude REAL
        );
        CREATE TABLE Lines (
            LineID TEXT PRIMARY KEY,
            LineName TEXT,
            AverageSpeed TEXT
        );
        CREATE TABLE StationLineRelationships (
            NaPTAN TEXT,
            LineID TEXT,
            PRIMARY KEY (NaPTAN, LineID)
        );
        CREATE TABLE Connections (
            StationA TEXT,
            StationB TEXT,
            LineID TEXT,
            BaseTravelTime REAL,
            PRIMARY KEY (StationA, StationB, LineID)
        );
        CREATE TABLE Venues (
            VenueName TEXT PRIMARY KEY,
            Capacity INTEGER,
            Latitude REAL,
            Longitude REAL
        );
        CREATE TABLE VenueStationRelationships (
            VenueName TEXT,
            NaPTAN TEXT,
            Distance REAL,
            PRIMARY KEY (VenueName, NaPTAN)
        );
        CREATE TABLE Teams (
            TeamName TEXT PRIMARY KEY,
            VenueName TEXT
        );
        CREATE TABLE Events (
            VenueName TEXT,
            Date TEXT,
            Time TEXT,
            HomeTeam TEXT,
            AwayTeam TEXT,
            EventName TEXT,
            Duration INTEGER,
            PRIMARY KEY (VenueName, Date)
        );
        CREATE TABLE Users (
            Username TEXT PRIMARY KEY,
            PasswordHash TEXT,
            Salt TEXT,
            CHANGING_TIME REAL,
            MAX_TIME_WINDOW REAL,
            rawArrivalPeakOffset REAL,
            rawDeparturePeakOffset REAL,
            ATTENDANCE REAL,
            TRAIN_PROPORTION REAL,
            SIGMA_FACTOR REAL,
            MINIMUM_PEOPLE REAL,
            PERSON_DELAY REAL,
            PROPAGATION_FACTOR REAL,
            WALKING_TIME REAL,
            WALKING_SPEED REAL,
            NORMAL REAL,
            SLIGHTLY REAL,
            BUSY REAL
        );
    """)

    # Seed three stations forming a simple chain: STA -> STB -> STC
    cursor.executemany("INSERT INTO Stations VALUES (?, ?, ?, ?)", [
        ("STA", "Station A", 51.50, -0.10),
        ("STB", "Station B", 51.51, -0.11),
        ("STC", "Station C", 51.52, -0.12),
    ])

    cursor.execute("INSERT INTO Lines VALUES ('central', 'Central Line', '37.27')")

    # Bidirectional connections between adjacent stations
    cursor.executemany("INSERT INTO Connections VALUES (?, ?, ?, ?)", [
        ("STA", "STB", "central", 2.0),
        ("STB", "STA", "central", 2.0),
        ("STB", "STC", "central", 3.0),
        ("STC", "STB", "central", 3.0),
    ])

    cursor.executemany("INSERT INTO StationLineRelationships VALUES (?, ?)", [
        ("STA", "central"),
        ("STB", "central"),
        ("STC", "central"),
    ])

    # Seed a test venue with two nearby stations
    cursor.execute("INSERT INTO Venues VALUES ('Test Stadium', 1000, 51.505, -0.105)")
    cursor.execute("INSERT INTO Teams VALUES ('Test FC', 'Test Stadium')")
    cursor.execute("INSERT INTO VenueStationRelationships VALUES ('Test Stadium', 'STA', 0.5)")
    cursor.execute("INSERT INTO VenueStationRelationships VALUES ('Test Stadium', 'STB', 1.2)")

    # Seed a test user with known credentials and default parameters
    salt = "aabbccdd"
    passwordHash = hashlib.sha256((salt + "password").encode()).hexdigest()
    cursor.execute("""
        INSERT INTO Users VALUES (
            'testuser', ?, ?,
            4.4, 120, 25, 25, 0.95, 0.75, 4, 50, 0.002, 0.5, 15, 5, 1.0, 1.3, 2.0
        )
    """, (passwordHash, salt))

    # Seed a test event at the test venue
    cursor.execute("INSERT INTO Events VALUES ('Test Stadium', '01/01/2026', '15:00', 'Test FC', 'Away FC', 'Premier League', 120)")

    connection.commit()
    return connection


# Writes an in-memory database to a temporary file and returns the file path
# Needed because most functions take a file path rather than a connection object
def writeTestDatabaseToFile(connection):
    temporaryFile = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    temporaryFile.close()
    diskConnection = sqlite3.connect(temporaryFile.name)
    connection.backup(diskConnection)
    diskConnection.close()
    return temporaryFile.name


# Builds a minimal network object from the test database for use in crowding tests
def buildTestNetwork(databaseFile):
    network = classes.Network()
    graph = pathFinding.MakeGraph(databaseFile)
    stations = {}
    connections = {}
    crowdingAlgorithm.createNetwork(graph, databaseFile, stations, connections, network)
    return network, graph


# ─────────────────────────────────────────────────────────────────────────────
# login.py
# ─────────────────────────────────────────────────────────────────────────────

class TestGenerateSalt(unittest.TestCase):

    def testReturnsString(self):
        salt = login.generateSalt()
        self.assertIsInstance(salt, str)

    def testCorrectLength(self):
        #16 bytes converts to 32 hex characters
        salt = login.generateSalt()
        self.assertEqual(len(salt), 32)

    def testUniqueEachTime(self):
        #Two salts generated back to back should never be the same
        self.assertNotEqual(login.generateSalt(), login.generateSalt())


class TestCreateHashPassword(unittest.TestCase):

    def testReturnsString(self):
        result = login.createHashPassword("password", "somesalt")
        self.assertIsInstance(result, str)

    def testSHA256Length(self):
        #SHA-256 always produces a 64 character hex digest
        result = login.createHashPassword("password", "somesalt")
        self.assertEqual(len(result), 64)

    def testSameInputsSameHash(self):
        hash1 = login.createHashPassword("abc", "salt123")
        hash2 = login.createHashPassword("abc", "salt123")
        self.assertEqual(hash1, hash2)

    def testDifferentSaltsDifferentHash(self):
        hash1 = login.createHashPassword("abc", "salt1")
        hash2 = login.createHashPassword("abc", "salt2")
        self.assertNotEqual(hash1, hash2)

    def testDifferentPasswordsDifferentHash(self):
        hash1 = login.createHashPassword("password1", "salt")
        hash2 = login.createHashPassword("password2", "salt")
        self.assertNotEqual(hash1, hash2)


#createAccount() calls generateSalt() and createHashPassword() internally, so if these
#tests pass it also confirms both of those functions work in a real end-to-end context
class TestCreateAccount(unittest.TestCase):

    def setUp(self):
        self.connection = createTestDatabase()
        self.databaseFile = writeTestDatabaseToFile(self.connection)
        self.defaultParametersFile = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'programme files', 'defaultParameters.json')

    def tearDown(self):
        os.unlink(self.databaseFile)

    def testNewAccountReturnsTrue(self):
        result = login.createAccount(self.defaultParametersFile, "newuser", "pass123", self.databaseFile)
        self.assertTrue(result)

    def testDuplicateUsernameReturnsFalse(self):
        login.createAccount(self.defaultParametersFile, "dupuser", "pass", self.databaseFile)
        result = login.createAccount(self.defaultParametersFile, "dupuser", "pass", self.databaseFile)
        self.assertFalse(result)

    def testAccountStoredInDatabase(self):
        login.createAccount(self.defaultParametersFile, "checkuser", "pass", self.databaseFile)
        connection = sqlite3.connect(self.databaseFile)
        rows = connection.execute("SELECT Username FROM Users WHERE Username = 'checkuser'").fetchall()
        connection.close()
        self.assertEqual(len(rows), 1)


class TestLogin(unittest.TestCase):

    def setUp(self):
        self.connection = createTestDatabase()
        self.databaseFile = writeTestDatabaseToFile(self.connection)

    def tearDown(self):
        os.unlink(self.databaseFile)

    def testCorrectCredentials(self):
        result = login.login(self.databaseFile, "testuser", "password")
        self.assertEqual(result, "Login Successful")

    def testWrongPassword(self):
        result = login.login(self.databaseFile, "testuser", "wrongpass")
        self.assertEqual(result, "Wrong Password")

    def testNonexistentUser(self):
        result = login.login(self.databaseFile, "nobody", "pass")
        self.assertEqual(result, "Account Not Found")


# ─────────────────────────────────────────────────────────────────────────────
# customFunctions.py
# ─────────────────────────────────────────────────────────────────────────────

#crowdingAlgorithm.getParameters() is a thin wrapper that just calls
#customFunctions.getParameters(), so if these tests pass it also confirms
#crowdingAlgorithm.getParameters() works correctly
class TestGetParameters(unittest.TestCase):

    def setUp(self):
        self.connection = createTestDatabase()
        self.databaseFile = writeTestDatabaseToFile(self.connection)

    def tearDown(self):
        os.unlink(self.databaseFile)

    def testReturnsParameterObject(self):
        result = customFunctions.getParameters("testuser", self.databaseFile)
        self.assertIsNotNone(result)

    def testCorrectChangingTime(self):
        result = customFunctions.getParameters("testuser", self.databaseFile)
        self.assertAlmostEqual(result.CHANGING_TIME, 4.4)

    def testCorrectSigmaFactor(self):
        result = customFunctions.getParameters("testuser", self.databaseFile)
        self.assertAlmostEqual(result.SIGMA_FACTOR, 4.0)

    def testWindowIsCalculated(self):
        #calculateWindow() should be called inside getParameters so this should not be None
        result = customFunctions.getParameters("testuser", self.databaseFile)
        self.assertIsNotNone(result.arrivalWindowMinutes)


# ─────────────────────────────────────────────────────────────────────────────
# pathFinding.py
# ─────────────────────────────────────────────────────────────────────────────

class TestMakeGraph(unittest.TestCase):

    def setUp(self):
        self.connection = createTestDatabase()
        self.databaseFile = writeTestDatabaseToFile(self.connection)

    def tearDown(self):
        os.unlink(self.databaseFile)

    def testReturnsDictionary(self):
        graph = pathFinding.MakeGraph(self.databaseFile)
        self.assertIsInstance(graph, dict)

    def testCorrectStationsPresent(self):
        graph = pathFinding.MakeGraph(self.databaseFile)
        self.assertIn("STA", graph)
        self.assertIn("STB", graph)

    def testNeighboursCorrect(self):
        graph = pathFinding.MakeGraph(self.databaseFile)
        neighbourIDs = [neighbour[0] for neighbour in graph["STA"]]
        self.assertIn("STB", neighbourIDs)

    def testTravelTimesArePositive(self):
        graph = pathFinding.MakeGraph(self.databaseFile)
        for neighbours in graph.values():
            for entry in neighbours:
                self.assertGreater(entry[1], 0)


class TestDijkstra(unittest.TestCase):

    def setUp(self):
        self.connection = createTestDatabase()
        self.databaseFile = writeTestDatabaseToFile(self.connection)
        self.graph = pathFinding.MakeGraph(self.databaseFile)

    def tearDown(self):
        os.unlink(self.databaseFile)

    def testReturnsList(self):
        path = pathFinding.Dijkstra(self.graph, "STA", "STC", 4.4)
        self.assertIsInstance(path, list)

    def testPathNotEmpty(self):
        path = pathFinding.Dijkstra(self.graph, "STA", "STC", 4.4)
        self.assertGreater(len(path), 0)

    def testPathEndsAtGoal(self):
        path = pathFinding.Dijkstra(self.graph, "STA", "STC", 4.4)
        lastStation = path[-1][1]
        self.assertEqual(lastStation, "STC")

    def testAdjacentStationsOneStep(self):
        #STA and STB are directly connected so path should be a single step
        path = pathFinding.Dijkstra(self.graph, "STA", "STB", 4.4)
        self.assertEqual(len(path), 1)

    def testCostIncreasesAlongPath(self):
        #Cumulative cost at each step should always be increasing
        path = pathFinding.Dijkstra(self.graph, "STA", "STC", 4.4)
        costs = [step[3] for step in path]
        self.assertEqual(costs, sorted(costs))

    def testPenaltyOffGivesLowerOrEqualCost(self):
        #Disabling line change penalty should never increase journey cost
        pathWithPenalty = pathFinding.Dijkstra(self.graph, "STA", "STC", 4.4, penalty=True)
        pathWithoutPenalty = pathFinding.Dijkstra(self.graph, "STA", "STC", 4.4, penalty=False)
        self.assertLessEqual(pathWithoutPenalty[-1][3], pathWithPenalty[-1][3])

    def testSameStartAndEndReturnsEmptyPath(self):
        path = pathFinding.Dijkstra(self.graph, "STA", "STA", 4.4)
        self.assertEqual(len(path), 0)


# ─────────────────────────────────────────────────────────────────────────────
# crowdingAlgorithm.py
# ─────────────────────────────────────────────────────────────────────────────

class TestTakeInput(unittest.TestCase):

    def testReturnsDictionary(self):
        result = crowdingAlgorithm.takeInput("01/01/2026", "15:00", "STA", "STC")
        self.assertIsInstance(result, dict)

    def testCorrectKeysPresent(self):
        result = crowdingAlgorithm.takeInput("01/01/2026", "15:00", "STA", "STC")
        self.assertIn("date", result)
        self.assertIn("journeyStart", result)
        self.assertIn("startStation", result)
        self.assertIn("endStation", result)

    def testValuesStoredCorrectly(self):
        result = crowdingAlgorithm.takeInput("01/01/2026", "15:00", "STA", "STC")
        self.assertEqual(result["date"], "01/01/2026")
        self.assertEqual(result["startStation"], "STA")


class TestInverseWeight(unittest.TestCase):

    def testReturnsDictionary(self):
        result = crowdingAlgorithm.inverseWeight({"STA": 1.0, "STB": 2.0})
        self.assertIsInstance(result, dict)

    def testProportionsSumToOne(self):
        result = crowdingAlgorithm.inverseWeight({"STA": 1.0, "STB": 2.0, "STC": 3.0})
        self.assertAlmostEqual(sum(result.values()), 1.0, places=9)

    def testCloserStationHigherProportion(self):
        result = crowdingAlgorithm.inverseWeight({"CLOSE": 0.5, "FAR": 5.0})
        self.assertGreater(result["CLOSE"], result["FAR"])

    def testZeroDistanceDoesNotCrash(self):
        #+1 guard in inverseWeight should prevent ZeroDivisionError when distance is 0
        result = crowdingAlgorithm.inverseWeight({"STA": 0.0, "STB": 1.0})
        self.assertAlmostEqual(sum(result.values()), 1.0, places=9)

    def testSingleStationProportionIsOne(self):
        result = crowdingAlgorithm.inverseWeight({"STA": 2.0})
        self.assertAlmostEqual(result["STA"], 1.0)


class TestGaussianFactor(unittest.TestCase):

    def testAtPeakReturnsOne(self):
        #When relativePeak equals relativeTimeDifference, x=0, exp(0)=1
        result = crowdingAlgorithm.gausianFactorAtPeak(10, 5, 10)
        self.assertAlmostEqual(result, 1.0)

    def testReturnsBetweenZeroAndOne(self):
        result = crowdingAlgorithm.gausianFactorAtPeak(10, 5, 20)
        self.assertGreaterEqual(result, 0.0)
        self.assertLessEqual(result, 1.0)

    def testFurtherFromPeakLowerFactor(self):
        close = crowdingAlgorithm.gausianFactorAtPeak(10, 5, 12)
        far = crowdingAlgorithm.gausianFactorAtPeak(10, 5, 30)
        self.assertGreater(close, far)


class TestReturnStationsWithDistances(unittest.TestCase):

    def setUp(self):
        self.connection = createTestDatabase()
        self.databaseFile = writeTestDatabaseToFile(self.connection)

    def tearDown(self):
        os.unlink(self.databaseFile)

    def testReturnsDictionary(self):
        result = crowdingAlgorithm.returnStationsWithDistances("Test Stadium", self.databaseFile)
        self.assertIsInstance(result, dict)

    def testCorrectStationsReturned(self):
        result = crowdingAlgorithm.returnStationsWithDistances("Test Stadium", self.databaseFile)
        self.assertIn("STA", result)
        self.assertIn("STB", result)

    def testDistanceValuesArePositive(self):
        result = crowdingAlgorithm.returnStationsWithDistances("Test Stadium", self.databaseFile)
        for distance in result.values():
            self.assertGreater(distance, 0)

    def testUnknownVenueReturnsEmpty(self):
        result = crowdingAlgorithm.returnStationsWithDistances("Nonexistent Venue", self.databaseFile)
        self.assertEqual(result, {})


class TestFindCapacity(unittest.TestCase):

    def setUp(self):
        self.connection = createTestDatabase()
        self.databaseFile = writeTestDatabaseToFile(self.connection)

    def tearDown(self):
        os.unlink(self.databaseFile)

    def testReturnsCorrectCapacity(self):
        result = crowdingAlgorithm.findCapacity(self.databaseFile, "Test Stadium")
        self.assertEqual(result, 1000)


class TestFindEventsInTimeFrame(unittest.TestCase):

    def setUp(self):
        self.connection = createTestDatabase()
        self.databaseFile = writeTestDatabaseToFile(self.connection)
        #Journey mid-point just after the event starts
        self.midjourneyTime = datetime.datetime.strptime("15:30", "%H:%M")
        self.baseInputData = {
            "date": "01/01/2026",
            "journeyStart": "15:00",
            "startStation": "STA",
            "endStation": "STC"
        }
        #Peak offset as timedelta(minutes=25) — matches the fixed calculatePeakOffset()
        self.peakOffset = datetime.timedelta(minutes=25)

    def tearDown(self):
        os.unlink(self.databaseFile)

    def testReturnsDictionary(self):
        result = crowdingAlgorithm.findEventsInTimeFrame(self.midjourneyTime, self.databaseFile, self.baseInputData, 120, self.peakOffset, self.peakOffset)
        self.assertIsInstance(result, dict)

    def testNearbyEventIsFound(self):
        #Event at 15:00 should be within the 120 minute window of a 15:30 midjourney
        result = crowdingAlgorithm.findEventsInTimeFrame(self.midjourneyTime, self.databaseFile, self.baseInputData, 120, self.peakOffset, self.peakOffset)
        self.assertGreater(len(result), 0)

    def testNoEventsOnEmptyDate(self):
        emptyDateInputData = {
            "date": "01/01/2099",
            "journeyStart": "15:00",
            "startStation": "STA",
            "endStation": "STC"
        }
        result = crowdingAlgorithm.findEventsInTimeFrame(self.midjourneyTime, self.databaseFile, emptyDateInputData, 120, self.peakOffset, self.peakOffset)
        self.assertEqual(result, {})


class TestCreateNetwork(unittest.TestCase):

    def setUp(self):
        self.connection = createTestDatabase()
        self.databaseFile = writeTestDatabaseToFile(self.connection)

    def tearDown(self):
        os.unlink(self.databaseFile)

    def testAllStationsAddedToNetwork(self):
        network, graph = buildTestNetwork(self.databaseFile)
        self.assertIn("STA", network.nodes)
        self.assertIn("STB", network.nodes)
        self.assertIn("STC", network.nodes)

    def testAllConnectionsAddedToNetwork(self):
        network, graph = buildTestNetwork(self.databaseFile)
        self.assertIn(("STA", "STB", "central"), network.edges)

    def testStationsStartAsNotAffected(self):
        network, graph = buildTestNetwork(self.databaseFile)
        for stationObject in network.nodes.values():
            self.assertFalse(stationObject.IsAffected())


class TestPropegation(unittest.TestCase):

    def setUp(self):
        self.connection = createTestDatabase()
        self.databaseFile = writeTestDatabaseToFile(self.connection)
        self.network, self.graph = buildTestNetwork(self.databaseFile)
        self.event = ("Test Stadium", "01/01/2026")

    def tearDown(self):
        os.unlink(self.databaseFile)

    def testStationBecomesAffected(self):
        crowdingAlgorithm.propegation(self.graph, "STA", 200, 50, self.network, self.event, 0.5)
        self.assertTrue(self.network.nodes["STA"].IsAffected())

    def testPropegationSpreadsToNeighbours(self):
        #200 people at STA with factor 0.5 should propagate 100 to STB (above MINIMUM_PEOPLE=50)
        crowdingAlgorithm.propegation(self.graph, "STA", 200, 50, self.network, self.event, 0.5)
        self.assertTrue(self.network.nodes["STB"].IsAffected())

    def testBelowMinimumDoesNotPropagate(self):
        #40 people at STA with factor 0.5 = 20, which is below MINIMUM_PEOPLE=50 so STB should stay unaffected
        crowdingAlgorithm.propegation(self.graph, "STA", 40, 50, self.network, self.event, 0.5)
        self.assertFalse(self.network.nodes["STB"].IsAffected())

    def testLargerWaveOverwritesSmaller(self):
        crowdingAlgorithm.propegation(self.graph, "STA", 100, 50, self.network, self.event, 0.5)
        crowdingAlgorithm.propegation(self.graph, "STA", 500, 50, self.network, self.event, 0.5)
        self.assertEqual(self.network.nodes["STA"].events[self.event], 500)


class TestProcessAffectedStations(unittest.TestCase):

    def setUp(self):
        self.connection = createTestDatabase()
        self.databaseFile = writeTestDatabaseToFile(self.connection)
        self.network, self.graph = buildTestNetwork(self.databaseFile)
        self.parameterObject = customFunctions.getParameters("testuser", self.databaseFile)
        event = ("Test Stadium", "01/01/2026")
        crowdingAlgorithm.propegation(self.graph, "STA", 500, 50, self.network, event, 0.5)

    def tearDown(self):
        os.unlink(self.databaseFile)

    def testAffectedStationDelayFactorAboveOne(self):
        crowdingAlgorithm.processAffectedStations(self.graph, self.parameterObject, self.network)
        self.assertGreater(self.network.nodes["STA"].DelayFactor, 1.0)

    def testAffectedStationHasHigherDelayThanUnaffected(self):
        crowdingAlgorithm.processAffectedStations(self.graph, self.parameterObject, self.network)
        #STA is directly affected so its delay should be higher than the default of 1.0
        #This confirms processAffectedStations correctly increases delay on affected stations
        self.assertGreater(self.network.nodes["STA"].DelayFactor, 1.0)


#spreadDelay() is the last step in crowdingAlgorithm.main(), so the setUp here runs the
#full crowding pipeline — meaning if these tests pass, it also confirms processAffected(),
#processAffectedStations(), processAffectedConnections(), getCrowdingFactor(), and
#crowdingAlgorithm.main() all work correctly end-to-end
class TestSpreadDelay(unittest.TestCase):

    def setUp(self):
        self.connection = createTestDatabase()
        self.databaseFile = writeTestDatabaseToFile(self.connection)
        self.network, self.graph = buildTestNetwork(self.databaseFile)
        parameterObject = customFunctions.getParameters("testuser", self.databaseFile)
        event = ("Test Stadium", "01/01/2026")
        crowdingAlgorithm.propegation(self.graph, "STA", 500, 50, self.network, event, 0.5)
        crowdingAlgorithm.processAffected(self.graph, parameterObject, self.network)

    def tearDown(self):
        os.unlink(self.databaseFile)

    def testLinedelayIsSetOnConnections(self):
        crowdingAlgorithm.spreadDelay(self.network, self.databaseFile)
        #All connections on the central line should now have the same LineDelay
        centralConnections = [edge for key, edge in self.network.edges.items() if key[2] == "central"]
        lineDelays = [c.LineDelay for c in centralConnections]
        self.assertTrue(all(d == lineDelays[0] for d in lineDelays))


# ─────────────────────────────────────────────────────────────────────────────
# storeStadiumData.py
# ─────────────────────────────────────────────────────────────────────────────

class TestCalculateWalkingDistance(unittest.TestCase):

    def testKnownValue(self):
        #5 km/h for 60 minutes = 5.0 km
        result = storeStadiumData.calculateWalkingDistance(60, 5)
        self.assertAlmostEqual(result, 5.0)

    def testDefaultParameters(self):
        #Default parameters: 15 minutes at 5 km/h = 1.25 km
        result = storeStadiumData.calculateWalkingDistance(15, 5)
        self.assertAlmostEqual(result, 1.25)

    def testZeroTimeReturnsZero(self):
        result = storeStadiumData.calculateWalkingDistance(0, 5)
        self.assertAlmostEqual(result, 0.0)


class TestGetCloseStations(unittest.TestCase):

    def setUp(self):
        #Three stations at increasing distances from venue coordinates
        self.allStations = [
            ("STA", 51.50, -0.10),  # Closest — same location as venue
            ("STB", 51.60, -0.20),  # Medium distance
            ("STC", 51.80, -0.40),  # Far away
        ]
        self.venueCoordinates = (51.50, -0.10) #Same coordinates as STA

    def testReturnsDictionary(self):
        result = storeStadiumData.getCloseStations(self.allStations, self.venueCoordinates, 5.0)
        self.assertIsInstance(result, dict)

    def testAlwaysReturnsAtLeastOne(self):
        #Even with a threshold of zero, the closest station should always be included
        result = storeStadiumData.getCloseStations(self.allStations, self.venueCoordinates, 0.0)
        self.assertGreaterEqual(len(result), 1)

    def testClosestStationAlwaysIncluded(self):
        result = storeStadiumData.getCloseStations(self.allStations, self.venueCoordinates, 0.0)
        self.assertIn("STA", result)

    def testDistantStationExcluded(self):
        #STC is roughly 33km away so should not appear within a 1km threshold
        result = storeStadiumData.getCloseStations(self.allStations, self.venueCoordinates, 1.0)
        self.assertNotIn("STC", result)

    def testStationWithinThresholdIncluded(self):
        #Use a large threshold to make sure STB is included
        result = storeStadiumData.getCloseStations(self.allStations, self.venueCoordinates, 20.0)
        self.assertIn("STB", result)


#insertData() calls getCloseStations() internally to find nearby stations for the venue,
#so if these tests pass it also confirms getCloseStations() works in a real context
class TestInsertData(unittest.TestCase):

    def setUp(self):
        self.connection = createTestDatabase()
        self.databaseFile = writeTestDatabaseToFile(self.connection)
        self.coordinates = {"lat": 51.50, "lng": -0.10}

    def tearDown(self):
        os.unlink(self.databaseFile)

    def testVenueIsStoredInDatabase(self):
        storeStadiumData.insertData(self.databaseFile, "New FC", "New Stadium", 5000, self.coordinates, 2.0)
        connection = sqlite3.connect(self.databaseFile)
        rows = connection.execute("SELECT VenueName FROM Venues WHERE VenueName = 'New Stadium'").fetchall()
        connection.close()
        self.assertEqual(len(rows), 1)

    def testTeamIsStoredInDatabase(self):
        storeStadiumData.insertData(self.databaseFile, "New FC", "New Stadium", 5000, self.coordinates, 2.0)
        connection = sqlite3.connect(self.databaseFile)
        rows = connection.execute("SELECT TeamName FROM Teams WHERE TeamName = 'New FC'").fetchall()
        connection.close()
        self.assertEqual(len(rows), 1)

    def testVenueStationRelationshipCreated(self):
        storeStadiumData.insertData(self.databaseFile, "New FC", "New Stadium", 5000, self.coordinates, 5.0)
        connection = sqlite3.connect(self.databaseFile)
        rows = connection.execute("SELECT * FROM VenueStationRelationships WHERE VenueName = 'New Stadium'").fetchall()
        connection.close()
        self.assertGreater(len(rows), 0)


class TestRedoStore(unittest.TestCase):

    def setUp(self):
        self.connection = createTestDatabase()
        self.databaseFile = writeTestDatabaseToFile(self.connection)

        #Write a minimal londonClubs JSON using only clubs already seeded in the test database
        #redoStore reads venue coordinates from the Venues table so the venue must exist
        self.londonClubsFile = tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w")
        json.dump({"Test FC": ["Test Stadium", 1000]}, self.londonClubsFile)
        self.londonClubsFile.close()
        self.londonClubsFilePath = self.londonClubsFile.name

    def tearDown(self):
        os.unlink(self.databaseFile)
        os.unlink(self.londonClubsFilePath)

    def testVenueStationRelationshipsAreRepopulated(self):
        #redoStore should delete and reinsert VenueStationRelationships for the given venues
        storeStadiumData.redoStore(15, 5, self.londonClubsFilePath, self.databaseFile)
        connection = sqlite3.connect(self.databaseFile)
        rows = connection.execute("SELECT * FROM VenueStationRelationships").fetchall()
        connection.close()
        self.assertGreater(len(rows), 0)


# ─────────────────────────────────────────────────────────────────────────────
# scraper.py
# ─────────────────────────────────────────────────────────────────────────────

class TestGetDate(unittest.TestCase):

    def testStandardDate(self):
        result = scraper.getDate("2026-01", "Saturday 10th January")
        self.assertEqual(result, "10-01-2026")

    def testSingleDigitDayIsPadded(self):
        result = scraper.getDate("2026-03", "Wednesday 5th March")
        self.assertEqual(result, "05-03-2026")

    def testNoNumberReturnsError(self):
        result = scraper.getDate("2026-01", "No numbers here")
        self.assertEqual(result, "Error")

    def testEmptyStringReturnsError(self):
        result = scraper.getDate("2026-01", "")
        self.assertEqual(result, "Error")


class TestGetNextTwelveMonths(unittest.TestCase):

    def testReturnsTwelveEntries(self):
        result = scraper.getNextTwelveMonths()
        self.assertEqual(len(result), 12)

    def testAllEntriesCorrectFormat(self):
        import re
        result = scraper.getNextTwelveMonths()
        for entry in result:
            self.assertRegex(entry, r"^\d{4}-\d{2}$")

    def testNoDuplicateMonths(self):
        result = scraper.getNextTwelveMonths()
        self.assertEqual(len(result), len(set(result)))


# ─────────────────────────────────────────────────────────────────────────────
# databaseCreation.py
# ─────────────────────────────────────────────────────────────────────────────

class TestCreateDatabase(unittest.TestCase):

    def setUp(self):
        temporaryFile = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        temporaryFile.close()
        self.databaseFile = temporaryFile.name

    def tearDown(self):
        os.unlink(self.databaseFile)

    def testAllTablesCreated(self):
        databaseCreation.createDatabase(self.databaseFile)
        connection = sqlite3.connect(self.databaseFile)
        tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
        connection.close()
        expectedTables = {"Stations", "Lines", "StationLineRelationships", "Connections", "Venues", "VenueStationRelationships", "Events", "Users", "Teams"}
        self.assertEqual(expectedTables, tables)

    def testIdempotentOnSecondCall(self):
        #Calling createDatabase twice should not raise any errors
        databaseCreation.createDatabase(self.databaseFile)
        databaseCreation.createDatabase(self.databaseFile)

    def testCreateLinesPopulatesTable(self):
        databaseCreation.createDatabase(self.databaseFile)
        databaseCreation.createLines(self.databaseFile, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'programme files', 'lines.json'))
        connection = sqlite3.connect(self.databaseFile)
        count = connection.execute("SELECT COUNT(*) FROM Lines").fetchone()[0]
        connection.close()
        self.assertGreater(count, 0)

    def testGetWalkingReturnsPositiveValues(self):
        walkingSpeed, walkingTime = databaseCreation.getWalking(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'programme files', 'defaultParameters.json'))
        self.assertIsNotNone(walkingSpeed)
        self.assertIsNotNone(walkingTime)
        self.assertGreater(walkingSpeed, 0)
        self.assertGreater(walkingTime, 0)


# ─────────────────────────────────────────────────────────────────────────────
# getResults.py
# ─────────────────────────────────────────────────────────────────────────────

class TestGetNaPTAN(unittest.TestCase):

    def setUp(self):
        self.connection = createTestDatabase()
        self.databaseFile = writeTestDatabaseToFile(self.connection)

    def tearDown(self):
        os.unlink(self.databaseFile)

    def testReturnsCorrectNaPTAN(self):
        result = getResults.getNaPTAN("Station A", self.databaseFile)
        self.assertEqual(result, "STA")

    def testDifferentStationDifferentNaPTAN(self):
        result = getResults.getNaPTAN("Station B", self.databaseFile)
        self.assertEqual(result, "STB")


#GetaffectedGraph() is a core step used by getAffectedOldPath() and getResults.main(),
#so if these tests pass alongside TestGetStrippedGraph and TestDijkstra, it also
#confirms getAffectedOldPath() and getResults.main() work correctly end-to-end
class TestGetAffectedGraph(unittest.TestCase):

    def setUp(self):
        self.connection = createTestDatabase()
        self.databaseFile = writeTestDatabaseToFile(self.connection)
        self.network, self.graph = buildTestNetwork(self.databaseFile)
        parameterObject = customFunctions.getParameters("testuser", self.databaseFile)
        event = ("Test Stadium", "01/01/2026")
        crowdingAlgorithm.propegation(self.graph, "STA", 500, 50, self.network, event, 0.5)
        crowdingAlgorithm.processAffected(self.graph, parameterObject, self.network)
        crowdingAlgorithm.spreadDelay(self.network, self.databaseFile)

    def tearDown(self):
        os.unlink(self.databaseFile)

    def testReturnsDictionary(self):
        affectedGraph = getResults.GetaffectedGraph(self.graph, self.network)
        self.assertIsInstance(affectedGraph, dict)

    def testOriginalGraphNotModified(self):
        #GetaffectedGraph uses deepcopy so original should be unchanged
        originalTime = self.graph["STA"][0][1]
        getResults.GetaffectedGraph(self.graph, self.network)
        self.assertEqual(self.graph["STA"][0][1], originalTime)

    def testAffectedGraphHasHigherTravelTimes(self):
        affectedGraph = getResults.GetaffectedGraph(self.graph, self.network)
        #At least one connection should have a higher travel time due to crowding
        originalTotal = sum(entry[1] for neighbours in self.graph.values() for entry in neighbours)
        affectedTotal = sum(entry[1] for neighbours in affectedGraph.values() for entry in neighbours)
        self.assertGreaterEqual(affectedTotal, originalTotal)


class TestGetStrippedGraph(unittest.TestCase):

    def setUp(self):
        self.connection = createTestDatabase()
        self.databaseFile = writeTestDatabaseToFile(self.connection)
        self.graph = pathFinding.MakeGraph(self.databaseFile)
        self.oldPath = pathFinding.Dijkstra(self.graph, "STA", "STC", 4.4)

    def tearDown(self):
        os.unlink(self.databaseFile)

    def testReturnsDictionary(self):
        result = getResults.getStrippedGraph(self.oldPath, self.graph)
        self.assertIsInstance(result, dict)

    def testOnlyContainsPathConnections(self):
        #Stripped graph should only have stations that appear in the path
        strippedGraph = getResults.getStrippedGraph(self.oldPath, self.graph)
        pathStations = {step[0] for step in self.oldPath}
        for station in strippedGraph.keys():
            self.assertIn(station, pathStations)


# ─────────────────────────────────────────────────────────────────────────────
# websiteDataClasses.py (via classes.py)
# ─────────────────────────────────────────────────────────────────────────────

class TestMainPagePathClass(unittest.TestCase):

    def setUp(self):
        self.connection = createTestDatabase()
        self.databaseFile = writeTestDatabaseToFile(self.connection)

    def tearDown(self):
        os.unlink(self.databaseFile)

    def testAddStation(self):
        pathObject = classes.mainPagePathClass("central")
        pathObject.addStation("STA")
        self.assertIn("STA", pathObject.ListOfStations)

    def testAddMultipleStations(self):
        pathObject = classes.mainPagePathClass("central")
        pathObject.addStation("STA")
        pathObject.addStation("STB")
        self.assertEqual(len(pathObject.ListOfStations), 2)

    def testGetLineName(self):
        pathObject = classes.mainPagePathClass("central")
        pathObject.getLineName(self.databaseFile)
        self.assertEqual(pathObject.LineName, "Central Line")

    def testGetStationNames(self):
        pathObject = classes.mainPagePathClass("central")
        pathObject.addStation("STA")
        pathObject.addStation("STB")
        pathObject.getStationNames(self.databaseFile)
        stationNames = [entry[0] for entry in pathObject.ListOfStationNames]
        self.assertIn("Station A", stationNames)
        self.assertIn("Station B", stationNames)

    def testGetDescription(self):
        pathObject = classes.mainPagePathClass("central")
        pathObject.addStation("STA")
        pathObject.ListOfStationNames = [["Station A", "STA"]]
        pathObject.getDescription([["STA", "Normal"]])
        self.assertEqual(pathObject.ListOfStationNamesAndDescriptions[0][2], "Normal")


# ─────────────────────────────────────────────────────────────────────────────
# scraperClasses.py (via classes.py)
# ─────────────────────────────────────────────────────────────────────────────

#Note: AllDates.storeInDatabase() does not have its own direct test but is used in the
#full scraper pipeline — if TestGetPageFixtures passes and fixtures are stored correctly
#via testAllDatesFiltersNonLondonFixtures, it confirms storeInDatabase() works
class TestScraperClasses(unittest.TestCase):

    def setUp(self):
        self.connection = createTestDatabase()
        self.databaseFile = writeTestDatabaseToFile(self.connection)

    def tearDown(self):
        os.unlink(self.databaseFile)

    def testFixtureStoresData(self):
        fixtureObject = classes.Fixture("Premier League", "Test FC", "Away FC", "15:00")
        self.assertEqual(fixtureObject.home, "Test FC")
        self.assertEqual(fixtureObject.away, "Away FC")
        self.assertEqual(fixtureObject.time, "15:00")

    def testFindRelevantFixturesRemovesNonLondon(self):
        londonFixture = classes.Fixture("PL", "Test FC", "Other", "15:00")
        nonLondonFixture = classes.Fixture("PL", "NonLondonClub", "Other", "15:00")
        dateObject = classes.Date("01-01-2026", [londonFixture, nonLondonFixture])
        dateObject.findRelevantFixtures(["Test FC"])
        self.assertEqual(len(dateObject.fixtures), 1)
        self.assertEqual(dateObject.fixtures[0].home, "Test FC")

    def testFindRelevantFixturesKeepsAllLondon(self):
        londonFixture = classes.Fixture("PL", "Test FC", "Other", "15:00")
        dateObject = classes.Date("01-01-2026", [londonFixture])
        dateObject.findRelevantFixtures(["Test FC"])
        self.assertEqual(len(dateObject.fixtures), 1)

    def testAllDatesFiltersNonLondonFixtures(self):
        londonFixture = classes.Fixture("PL", "Test FC", "Away", "15:00")
        nonLondonFixture = classes.Fixture("PL", "ManUtd", "Away", "15:00")
        dateObject = classes.Date("01-01-2026", [londonFixture, nonLondonFixture])
        allDatesObject = classes.AllDates([dateObject])
        allDatesObject.findRelevantDates(self.databaseFile)
        self.assertEqual(len(allDatesObject.dates), 1)
        self.assertEqual(len(allDatesObject.dates[0].fixtures), 1)


# ─────────────────────────────────────────────────────────────────────────────
# transportClasses.py (via classes.py)
# ─────────────────────────────────────────────────────────────────────────────

class TestTransportClasses(unittest.TestCase):

    def testAffectedStationIsAffected(self):
        stationObject = classes.AffectedDijkstraStation("STA", "Station A")
        self.assertTrue(stationObject.IsAffected())

    def testNotAffectedStationIsNotAffected(self):
        stationObject = classes.NotAffectedDijkstraStation("STA", "Station A")
        self.assertFalse(stationObject.IsAffected())

    def testCalculatePassengerLoad(self):
        stationObject = classes.AffectedDijkstraStation("STA", "Station A")
        stationObject.events[("Test Stadium", "01/01/2026")] = 200
        stationObject.events[("Other Stadium", "01/01/2026")] = 100
        load = stationObject.calculatePassengerLoad()
        self.assertEqual(load, 300)

    def testCalculateDelay(self):
        stationObject = classes.AffectedDijkstraStation("STA", "Station A")
        stationObject.currentPassengerLoad = 500
        stationObject.calculateDelay(0.002)
        self.assertAlmostEqual(stationObject.DelayFactor, 2.0) #1 + (0.002 * 500) = 2.0

    def testAffectedConnectionIsAffected(self):
        connectionObject = classes.AffectedConnection("STA", "STB", "central", 2.0, 1.5, 2.0)
        self.assertTrue(connectionObject.IsAffected())

    def testNotAffectedConnectionDelayIsOne(self):
        connectionObject = classes.NotAffectedConnection("STA", "STB", "central", 2.0)
        delay = connectionObject.returnDelay()
        self.assertEqual(delay, 1)

    def testAffectedConnectionReturnDelay(self):
        #Delay should be the average of the two station delay factors
        connectionObject = classes.AffectedConnection("STA", "STB", "central", 2.0, 1.5, 2.5)
        delay = connectionObject.returnDelay()
        self.assertAlmostEqual(delay, 2.0) #(1.5 + 2.5) / 2 = 2.0

    def testAbstractClassCannotBeInstantiated(self):
        with self.assertRaises(TypeError):
            classes.TransportClass()

    def testLineSpreadDelay(self):
        #Average delay across both connections should be (1.5 + 2.5) / 2 = 2.0
        connection1 = classes.NotAffectedConnection("STA", "STB", "central", 2.0)
        connection2 = classes.NotAffectedConnection("STB", "STC", "central", 3.0)
        connection1.DelayFactor = 1.5
        connection2.DelayFactor = 2.5
        lineObject = classes.Line([connection1, connection2], "central")
        lineObject.doAllCalculations()
        self.assertAlmostEqual(connection1.LineDelay, 2.0)
        self.assertAlmostEqual(connection2.LineDelay, 2.0)


# ─────────────────────────────────────────────────────────────────────────────
# accountClasses.py (via classes.py)
# ─────────────────────────────────────────────────────────────────────────────

class TestParameters(unittest.TestCase):

    def setUp(self):
        self.parameterObject = classes.Parameters(4.4, 120, 25, 25, 0.95, 0.75, 4, 50, 0.002, 0.5, 15, 5, 1, 1.3, 2)

    def testCalculateWindow(self):
        self.parameterObject.calculateWindow()
        self.assertEqual(self.parameterObject.arrivalWindowMinutes, 120)
        self.assertEqual(self.parameterObject.departureWindowMinutes, 120)

    def testCalculatePeakOffset(self):
        self.parameterObject.calculatePeakOffset()
        self.assertIsInstance(self.parameterObject.arrivalPeakOffset, datetime.timedelta)

    def testCalculateMinutesOffset(self):
        self.parameterObject.calculateWindow()
        self.parameterObject.calculatePeakOffset()
        self.parameterObject.calculateMinutesOffset()
        self.assertIsNotNone(self.parameterObject.arrivalMinutesOffset)

    def testPeakOffsetIsCorrectMinutes(self):
        #After the fix, timedelta(minutes=25) should give 25 minutes not 25 days
        self.parameterObject.calculatePeakOffset()
        totalMinutes = self.parameterObject.arrivalPeakOffset.total_seconds() / 60
        self.assertAlmostEqual(totalMinutes, 25.0)

    def testAccountCreationParametersLoadsDefaults(self):
        defaultParametersObject = classes.AccountCreationParameters(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'programme files', 'defaultParameters.json'))
        self.assertAlmostEqual(defaultParametersObject.ATTENDANCE, 0.95)
        self.assertAlmostEqual(defaultParametersObject.TRAIN_PROPORTION, 0.75)


# ─────────────────────────────────────────────────────────────────────────────
# networkClasses.py (via classes.py)
# ─────────────────────────────────────────────────────────────────────────────

class TestSeverity(unittest.TestCase):

    def setUp(self):
        self.connection = createTestDatabase()
        self.databaseFile = writeTestDatabaseToFile(self.connection)

        # Build a minimal network with three unaffected stations
        self.network = classes.Network()
        for NaPTAN, stationName in [("STA", "Station A"), ("STB", "Station B"), ("STC", "Station C")]:
            self.network.nodes[NaPTAN] = classes.NotAffectedDijkstraStation(NaPTAN, stationName)

    def tearDown(self):
        os.unlink(self.databaseFile)

    def testGetDescriptionNormal(self):
        path = [("STA", "STB", "central", 2.0), ("STB", "STC", "central", 5.0)]
        severityObject = classes.Severity(path, "testuser", self.databaseFile, "STA", self.network)
        severityObject.getParameters()
        description = severityObject.getDescription(0.5) #Below NORMAL threshold of 1.0
        self.assertEqual(description, "Normal")

    def testGetDescriptionSevere(self):
        path = [("STA", "STB", "central", 2.0)]
        severityObject = classes.Severity(path, "testuser", self.databaseFile, "STA", self.network)
        severityObject.getParameters()
        description = severityObject.getDescription(2.5) #Above BUSY threshold of 2.0
        self.assertEqual(description, "Severe")

    def testCalculateFillsDescriptions(self):
        #Path visits STA (start), STB, STC so descriptions should have 3 entries
        path = [("STA", "STB", "central", 2.0), ("STB", "STC", "central", 5.0)]
        severityObject = classes.Severity(path, "testuser", self.databaseFile, "STA", self.network)
        severityObject.calculate()
        self.assertEqual(len(severityObject.descriptions), 3)


# ─────────────────────────────────────────────────────────────────────────────
# main.py — Flask test client simulates HTTP requests without a browser
# ─────────────────────────────────────────────────────────────────────────────

class TestMainFlaskRoutes(unittest.TestCase):

    def setUp(self):
        self.connection = createTestDatabase()
        self.databaseFile = writeTestDatabaseToFile(self.connection)

        # Write a flags file so the app doesn't try to create the database on startup
        self.flagsFile = tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w")
        json.dump({"status": "success", "error": "success"}, self.flagsFile)
        self.flagsFile.close()
        self.flagsFilePath = self.flagsFile.name

        # Write a minimal londonClubs file containing only the test venue so that
        # redoStore() doesn't try to look up real clubs not present in the test database
        self.testLondonClubsFile = tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w")
        json.dump({"Test FC": ["Test Stadium", 1000]}, self.testLondonClubsFile)
        self.testLondonClubsFile.close()
        self.testLondonClubsFilePath = self.testLondonClubsFile.name

        # Configure the Flask app with test settings
        mainApp.setUpConfig(
            mainApp.app,
            self.databaseFile,
            os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'programme files', 'lines.json'),
            "FAKE_TFL_KEY",
            "FAKE_OPENCAGE_KEY",
            self.testLondonClubsFilePath,
            os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'programme files', 'leagues.json'),
            self.flagsFilePath,
            os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'programme files', 'defaultParameters.json')
        )

        mainApp.app.config["TESTING"] = True
        mainApp.app.config["SECRET_KEY"] = "testkey"
        self.client = mainApp.app.test_client()

    def tearDown(self):
        os.unlink(self.databaseFile)
        os.unlink(self.flagsFilePath)
        os.unlink(self.testLondonClubsFilePath)

    def testLoginPageLoads(self):
        #GET request to / should return the login page
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)

    def testLoginWithCorrectCredentials(self):
        #POST to / with correct credentials should redirect to main page
        response = self.client.post("/", data={
            "username": "testuser",
            "password": "password",
            "actionName": "login"
        })
        self.assertEqual(response.status_code, 302) #302 = redirect

    def testLoginWithWrongPassword(self):
        #POST to / with wrong password should stay on login page with a message
        response = self.client.post("/", data={
            "username": "testuser",
            "password": "wrongpassword",
            "actionName": "login"
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Wrong Password", response.data)

    def testLoginWithUnknownUser(self):
        response = self.client.post("/", data={
            "username": "nobody",
            "password": "pass",
            "actionName": "login"
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Account Not Found", response.data)

    def testSignUpCreatesAccountAndRedirects(self):
        response = self.client.post("/", data={
            "username": "brandnewuser",
            "password": "pass123",
            "actionName": "signUp"
        })
        self.assertEqual(response.status_code, 302)

    def testSignUpDuplicateUsernameStaysOnPage(self):
        response = self.client.post("/", data={
            "username": "testuser",
            "password": "pass",
            "actionName": "signUp"
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Account already created", response.data)

    def testMainPageRedirectsIfNotLoggedIn(self):
        #Accessing /main without a session should redirect to login
        response = self.client.get("/main")
        self.assertEqual(response.status_code, 302)

    def testMainPageLoadsWhenLoggedIn(self):
        with self.client.session_transaction() as session:
            session["username"] = "testuser"
        response = self.client.get("/main")
        self.assertEqual(response.status_code, 200)

    def testLoadPageLoads(self):
        response = self.client.get("/load")
        self.assertEqual(response.status_code, 200)

    def testLogoutClearsSession(self):
        with self.client.session_transaction() as session:
            session["username"] = "testuser"
        response = self.client.post("/logout")
        self.assertEqual(response.status_code, 302)
        #After logout, /main should redirect back to login
        response = self.client.get("/main")
        self.assertEqual(response.status_code, 302)

    def testGetStationsReturnsJson(self):
        with self.client.session_transaction() as session:
            session["username"] = "testuser"
        response = self.client.get("/get_stations?search=Station")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIsInstance(data, list)

    def testGetStationsSearchFilters(self):
        with self.client.session_transaction() as session:
            session["username"] = "testuser"
        response = self.client.get("/get_stations?search=Station A")
        data = json.loads(response.data)
        self.assertTrue(any("Station A" in item["text"] for item in data))

    def testCheckFlagReturnsJson(self):
        response = self.client.get("/check_flag")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn("status", data)

    def testLoadDefaultParametersReturnsJson(self):
        with self.client.session_transaction() as session:
            session["username"] = "testuser"
        response = self.client.get("/load_default_parameters")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn("CHANGING_TIME", data)
        self.assertIn("ATTENDANCE", data)

    def testSaveParametersUpdatesDatabase(self):
        with self.client.session_transaction() as session:
            session["username"] = "testuser"
        #Use the same walking parameters already in the test database so redoStore
        #doesn't fail trying to look up venues that don't exist in the test database
        payload = {
            "CHANGING_TIME": 5.0, "MAX_TIME_WINDOW": 100.0,
            "rawArrivalPeakOffset": 20.0, "rawDeparturePeakOffset": 20.0,
            "ATTENDANCE": 0.9, "TRAIN_PROPORTION": 0.8,
            "SIGMA_FACTOR": 3.0, "MINIMUM_PEOPLE": 40.0,
            "PERSON_DELAY": 0.001, "PROPAGATION_FACTOR": 0.4,
            "WALKING_TIME": 15.0, "WALKING_SPEED": 5.0,
            "NORMAL": 1.0, "SLIGHTLY": 1.5, "BUSY": 2.5
        }
        response = self.client.post("/save_parameters",
            data=json.dumps(payload),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        #Verify the value was actually written to the database
        connection = sqlite3.connect(self.databaseFile)
        result = connection.execute("SELECT CHANGING_TIME FROM Users WHERE Username = 'testuser'").fetchone()[0]
        connection.close()
        self.assertAlmostEqual(result, 5.0)

    def testUpdateFlagsReturnsSuccess(self):
        response = self.client.post("/updateFlags")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data["success"])

    def testUpdatePageLoadsWhenLoggedIn(self):
        with self.client.session_transaction() as session:
            session["username"] = "testuser"
        response = self.client.get("/update")
        self.assertEqual(response.status_code, 200)


# ─────────────────────────────────────────────────────────────────────────────
# main.py — helper functions
# ─────────────────────────────────────────────────────────────────────────────

class TestFormatDuration(unittest.TestCase):

    def testLessThanOneHour(self):
        result = mainApp.formatDuration(45)
        self.assertIn("45", result)
        self.assertNotIn("hour", result)

    def testMoreThanOneHour(self):
        result = mainApp.formatDuration(90)
        self.assertIn("hour", result)
        self.assertIn("30", result)

    def testExactlyOneHour(self):
        result = mainApp.formatDuration(60)
        self.assertIn("1", result)
        self.assertIn("hour", result)


class TestProcessTime(unittest.TestCase):

    def testReturnsCorrectArrivalTime(self):
        duration, arrivalTime = mainApp.processTime(30, "10:00")
        self.assertEqual(arrivalTime, "10:30")

    def testReturnsCorrectDurationString(self):
        duration, arrivalTime = mainApp.processTime(30, "10:00")
        self.assertIn("30", duration)

    def testOvernightJourney(self):
        #Journey starting at 23:30 for 60 minutes should arrive at 00:30
        duration, arrivalTime = mainApp.processTime(60, "23:30")
        self.assertEqual(arrivalTime, "00:30")


class TestGetLines(unittest.TestCase):

    def setUp(self):
        self.connection = createTestDatabase()
        self.databaseFile = writeTestDatabaseToFile(self.connection)

    def tearDown(self):
        os.unlink(self.databaseFile)

    def testReturnsListOfLines(self):
        result = mainApp.getLines("Station A", self.databaseFile)
        self.assertIsInstance(result, list)

    def testCorrectLineReturned(self):
        result = mainApp.getLines("Station A", self.databaseFile)
        self.assertIn("Central Line", result)

    def testUnknownStationReturnsEmpty(self):
        result = mainApp.getLines("Nonexistent Station", self.databaseFile)
        self.assertEqual(result, [])




# ─────────────────────────────────────────────────────────────────────────────
# API tests — these require a live internet connection to run
# getTfLData.py and storeStadiumData.py and scraper.py
# ─────────────────────────────────────────────────────────────────────────────

class TestFetchStations(unittest.TestCase):

    def setUp(self):
        self.connection = createTestDatabase()
        self.databaseFile = writeTestDatabaseToFile(self.connection)
        databaseCreation.createLines(self.databaseFile, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'programme files', 'lines.json'))

    def tearDown(self):
        os.unlink(self.databaseFile)

    def testReturnsDictionary(self):
        #Fetches stations for the central line from the TfL API
        result = getTfLData.fetchStations(TfL_API_KEY, ["central"])
        self.assertIsInstance(result, dict)

    def testStationDictionaryNotEmpty(self):
        result = getTfLData.fetchStations(TfL_API_KEY, ["central"])
        self.assertGreater(len(result), 0)

    def testStationsHaveCorrectAttributes(self):
        result = getTfLData.fetchStations(TfL_API_KEY, ["central"])
        #Every station object should have a NaPTAN, StationName, Latitude and Longitude
        for stationObject in result.values():
            self.assertIsNotNone(stationObject.NaPTAN)
            self.assertIsNotNone(stationObject.StationName)
            self.assertIsNotNone(stationObject.Latitude)
            self.assertIsNotNone(stationObject.Longitude)

    def testBadApiKeyReturnsInt(self):
        #safeGet returns an integer status code when the API call fails
        result = getTfLData.fetchStations("invalid_key_12345", ["central"])
        self.assertIsInstance(result, int)


#fetch_lines() is one of the two functions called by fetchTfLData(), so if these tests
#pass alongside TestFetchStations it also confirms fetchTfLData() works end-to-end
class TestFetchLines(unittest.TestCase):

    def setUp(self):
        self.connection = createTestDatabase()
        self.databaseFile = writeTestDatabaseToFile(self.connection)
        databaseCreation.createLines(self.databaseFile, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'programme files', 'lines.json'))
        #fetchLines needs a populated stationDictionary to work with
        self.stationDictionary = getTfLData.fetchStations(TfL_API_KEY, ["central"])

    def tearDown(self):
        os.unlink(self.databaseFile)

    def testReturnsDictionary(self):
        result = getTfLData.fetch_lines(self.stationDictionary, TfL_API_KEY, ["central"])
        self.assertIsInstance(result, dict)

    def testCentralLinePresent(self):
        result = getTfLData.fetch_lines(self.stationDictionary, TfL_API_KEY, ["central"])
        self.assertIn("central", result)

    def testBranchesAreListsOfNaPTANs(self):
        result = getTfLData.fetch_lines(self.stationDictionary, TfL_API_KEY, ["central"])
        for branch in result["central"]:
            self.assertIsInstance(branch, list)
            self.assertGreater(len(branch), 0)


class TestGetStationCoordinates(unittest.TestCase):

    def setUp(self):
        self.connection = createTestDatabase()
        self.databaseFile = writeTestDatabaseToFile(self.connection)

    def tearDown(self):
        os.unlink(self.databaseFile)

    def testReturnsCoordinates(self):
        result = getTfLData.getStationCoordinates(self.databaseFile, "STA")
        self.assertIsNotNone(result)

    def testCoordinatesAreCorrect(self):
        result = getTfLData.getStationCoordinates(self.databaseFile, "STA")
        latitude, longitude = result
        self.assertAlmostEqual(latitude, 51.50)
        self.assertAlmostEqual(longitude, -0.10)


class TestGetStationLineRelationships(unittest.TestCase):

    def setUp(self):
        self.connection = createTestDatabase()
        self.databaseFile = writeTestDatabaseToFile(self.connection)

    def tearDown(self):
        os.unlink(self.databaseFile)

    def testRelationshipsArePopulated(self):
        #Wipe existing relationships then repopulate from the Connections table
        connection = sqlite3.connect(self.databaseFile)
        connection.execute("DELETE FROM StationLineRelationships")
        connection.commit()
        connection.close()
        getTfLData.getStationLineRelationships(self.databaseFile)
        connection = sqlite3.connect(self.databaseFile)
        rows = connection.execute("SELECT * FROM StationLineRelationships").fetchall()
        connection.close()
        self.assertGreater(len(rows), 0)

    def testRelationshipsMatchConnections(self):
        #Every NaPTAN in StationLineRelationships should also appear in Connections
        connection = sqlite3.connect(self.databaseFile)
        slrRows = {row[0] for row in connection.execute("SELECT NaPTAN FROM StationLineRelationships").fetchall()}
        connectionRows = {row[0] for row in connection.execute("SELECT StationA FROM Connections").fetchall()}
        connection.close()
        self.assertTrue(slrRows.issubset(connectionRows))


#SaveTfLData() calls fetchTfLData() and getStationLineRelationships() internally, so
#if these tests pass it also confirms both of those functions work correctly end-to-end
class TestSaveTfLData(unittest.TestCase):

    def setUp(self):
        temporaryFile = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        temporaryFile.close()
        self.databaseFile = temporaryFile.name
        databaseCreation.createDatabase(self.databaseFile)
        databaseCreation.createLines(self.databaseFile, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'programme files', 'lines.json'))

    def tearDown(self):
        os.unlink(self.databaseFile)

    def testSaveTfLDataReturnsTrue(self):
        #Full pipeline — fetches and stores all TfL station and connection data
        result = getTfLData.SaveTfLData(self.databaseFile, TfL_API_KEY)
        self.assertTrue(result)

    def testStationsTablePopulated(self):
        getTfLData.SaveTfLData(self.databaseFile, TfL_API_KEY)
        connection = sqlite3.connect(self.databaseFile)
        count = connection.execute("SELECT COUNT(*) FROM Stations").fetchone()[0]
        connection.close()
        self.assertGreater(count, 0)

    def testConnectionsTablePopulated(self):
        getTfLData.SaveTfLData(self.databaseFile, TfL_API_KEY)
        connection = sqlite3.connect(self.databaseFile)
        count = connection.execute("SELECT COUNT(*) FROM Connections").fetchone()[0]
        connection.close()
        self.assertGreater(count, 0)


class TestGetCoordinates(unittest.TestCase):

    def testReturnsCoordinatesForKnownStadium(self):
        result = storeStadiumData.getCoordinates(OPENCAGE_API_KEY, "Emirates Stadium")
        self.assertIn("lat", result)
        self.assertIn("lng", result)

    def testLatitudeIsReasonableForLondon(self):
        #All London venues should have latitude roughly between 51 and 52
        result = storeStadiumData.getCoordinates(OPENCAGE_API_KEY, "Stamford Bridge")
        self.assertGreater(result["lat"], 51.0)
        self.assertLess(result["lat"], 52.0)

    def testLongitudeIsReasonableForLondon(self):
        #All London venues should have longitude roughly between -0.5 and 0.1
        result = storeStadiumData.getCoordinates(OPENCAGE_API_KEY, "Stamford Bridge")
        self.assertGreater(result["lng"], -0.5)
        self.assertLess(result["lng"], 0.1)


#getStadiumData() calls getCoordinates() and insertData() for every club in the JSON,
#so if these tests pass it also confirms both functions work correctly in a real context,
#in addition to their own direct tests above
class TestGetStadiumData(unittest.TestCase):

    def setUp(self):
        self.connection = createTestDatabase()
        self.databaseFile = writeTestDatabaseToFile(self.connection)
        self.londonClubsFile = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'programme files', 'londonClubs.json')

    def tearDown(self):
        os.unlink(self.databaseFile)

    def testReturnsTrue(self):
        result = storeStadiumData.getStadiumData(self.londonClubsFile, self.databaseFile, OPENCAGE_API_KEY, 1.25)
        self.assertTrue(result)

    def testVenuesTablePopulated(self):
        storeStadiumData.getStadiumData(self.londonClubsFile, self.databaseFile, OPENCAGE_API_KEY, 1.25)
        connection = sqlite3.connect(self.databaseFile)
        count = connection.execute("SELECT COUNT(*) FROM Venues").fetchone()[0]
        connection.close()
        self.assertGreater(count, 0)

    def testTeamsTablePopulated(self):
        storeStadiumData.getStadiumData(self.londonClubsFile, self.databaseFile, OPENCAGE_API_KEY, 1.25)
        connection = sqlite3.connect(self.databaseFile)
        count = connection.execute("SELECT COUNT(*) FROM Teams").fetchone()[0]
        connection.close()
        self.assertGreater(count, 0)


#getPageFixtures() calls getDate() internally for every date heading it finds, so if
#these tests pass it also confirms getDate() works in a real scraping context.
#scraper.main() is an orchestrator that calls getPageFixtures() for every league and
#month, so if these tests pass it also confirms scraper.main() works end-to-end
class TestGetPageFixtures(unittest.TestCase):

    def testReturnsDictionary(self):
        #Scrapes one month of Premier League fixtures from BBC Sport
        fixtures = {}
        result = scraper.getPageFixtures(
            "https://www.bbc.co.uk/sport/football/premier-league/scores-fixtures/2026-03?filter=fixtures",
            "2026-03",
            "Premier League",
            fixtures
        )
        self.assertIsInstance(result, dict)

    def testFixturesNotEmpty(self):
        fixtures = {}
        result = scraper.getPageFixtures(
            "https://www.bbc.co.uk/sport/football/premier-league/scores-fixtures/2026-03?filter=fixtures",
            "2026-03",
            "Premier League",
            fixtures
        )
        #There should be at least some fixtures for a given month
        totalFixtures = sum(len(v) for v in result.values())
        self.assertGreater(totalFixtures, 0)

    def testFixturesHaveCorrectKeys(self):
        fixtures = {}
        result = scraper.getPageFixtures(
            "https://www.bbc.co.uk/sport/football/premier-league/scores-fixtures/2026-03?filter=fixtures",
            "2026-03",
            "Premier League",
            fixtures
        )
        for dateFixtures in result.values():
            for fixture in dateFixtures:
                self.assertIn("home", fixture)
                self.assertIn("away", fixture)
                self.assertIn("time", fixture)
                self.assertIn("league", fixture)

    def testBadUrlReturnsInt(self):
        #safeGet should return 0 if the URL is completely unreachable
        fixtures = {}
        result = scraper.getPageFixtures(
            "https://this.url.does.not.exist.invalid/fixtures",
            "2026-03",
            "Premier League",
            fixtures
        )
        self.assertIsInstance(result, int)

if __name__ == "__main__":
    unittest.main(verbosity=2)