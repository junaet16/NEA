import sys
import os
import types
import sqlite3
import unittest
import math
import hashlib
import tempfile
import datetime


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
import classes


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
# scraperClasses.py (via classes.py)
# ─────────────────────────────────────────────────────────────────────────────

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


if __name__ == "__main__":
    unittest.main(verbosity=2)