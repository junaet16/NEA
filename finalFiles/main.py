from flask import Flask, render_template, request, session, redirect, url_for, jsonify
import login
import sqlite3
from datetime import datetime, timedelta
import getResults
import classes
from pathlib import Path
import databaseCreation
import threading
import json
import storeStadiumData


# Flask app initialisation
app = Flask(__name__)
app.secret_key = "VERY_SECRET_KEY" # Needed for session management


# Makes these accessible anywhere in the app
def setUpConfig(
        app,
        databaseFile,
        LinesjsonFile,
        TfL_API_KEY,
        OPENCAGE_API_KEY,
        londonjsonFile,
        leaguesjsonFile,
        flagsFile,
        defaultParametersFile
):
    """
    Sets up all configuration variables in Flask's config dictionary.
    """
    app.config["DATABASE_FILE"] = databaseFile
    app.config["LINES_JSON_FILE"] = LinesjsonFile
    app.config["TFL_API_KEY"] = TfL_API_KEY
    app.config["OPENCAGE_API_KEY"] = OPENCAGE_API_KEY
    app.config["LONDONJSON_FILE"] = londonjsonFile
    app.config["LEAGUES_JSON_FILE"] = leaguesjsonFile
    app.config["FLAGS_FILE"] = flagsFile
    app.config["DEFAULT_PARAMETERS_FILE"] = defaultParametersFile


# Login / Signup Page
@app.route('/', methods=['GET', 'POST'])
def loginPage():
    """
    Displays the login page. Handles login and signup requests.
    Creates the database if it doesn't exist.
    """
    databaseFile = app.config["DATABASE_FILE"]
    flagsFile = app.config["FLAGS_FILE"]
    defaultParametersFile = app.config["DEFAULT_PARAMETERS_FILE"]
    message = None

    # Store previous page URL in session (used for redirects later)
    session["previousPage"] = request.url

    # Check if database exists
    databaseFilePath = Path(databaseFile)
    if not databaseFilePath.exists():
        # Create flags file if it doesn't exist
        flagsPath = Path(flagsFile)

        if not flagsPath.exists():
            with open(flagsFile, "w") as file:
                json.dump({"databaseCreated": False}, file)

        # Create database in a separate thread to avoid blocking and to allow for a waiting page to load
        threading.Thread(target=createDatabase).start()
        return redirect(url_for("loadPage"))

    # Wipe flags file if database exists
    with open(flagsFile, "w") as flag_file:
        pass #Wipe

    # Handle POST requests (login/signup)
    if request.method == 'POST':
        action = request.form.get('actionName')
        username = request.form.get('username')
        password = request.form.get('password')

        if action == 'login':
            loginMessage = login.login(databaseFile, username, password)
            if loginMessage == "Login Successful":
                session["username"] = username
                return redirect(url_for("mainPage"))
            else:
                message = loginMessage
        elif action == 'signUp':
            accountMade = login.createAccount(defaultParametersFile, username, password, databaseFile)
            if accountMade:
                session["username"] = username
                return redirect(url_for("mainPage"))
            else:
                message = "Account already created"
    return render_template("login.html", message=message)


# Loading Page
@app.route('/load', methods=['GET', 'POST'])
def loadPage():
    """
    Simple page to show when database is being created or updated.
    """
    return render_template("loading.html")


# Main Journey Planning Page
@app.route('/main', methods=['GET', 'POST']) #Need to uncomment out the validation for correct time
def mainPage():
    # Redirect to login if not logged in
    if "username" not in session:
        return redirect(url_for("loginPage"))

    databaseFile = app.config["DATABASE_FILE"]
    username = session["username"]

    # Initialise variables for template
    error = None
    startStationLines = None
    endStationLines = None
    formattedOldPath = None
    formattedNewPath = None
    oldPathTime = None
    oldPathArrival = None
    newPathTime = None
    newPathArrival = None

    if request.method == 'POST':
        if "updateButton" in request.form:
            # Redirect to update parameters page
            return redirect(url_for("updatePage"))
        else:
            # Get form input
            start = request.form.get('start')
            end = request.form.get('end')
            date = request.form.get('date')
            time = request.form.get('time')
            selectedTime = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")

            if start == end:
                error = "Start and end stations must be different"
            #ADD ELIF STATEMENT HERE to check if the selected time is before the current time
            else:
                # Format date for getResults
                dateObject = datetime.strptime(date, "%Y-%m-%d")
                passInDate = dateObject.strftime("%d/%m/%Y")

                # Get line information for dropdowns
                startStationLines = getLines(start, databaseFile)
                endStationLines = getLines(end, databaseFile)

                # Calculate journey paths
                resultsObject = getResults.main(passInDate, time, start, end, databaseFile, username)

                # Old Path (Affected)
                affectedOldPath = resultsObject.affectedOldPath
                affectedOldPathDesriptions = resultsObject.affectedOldPathDesriptions
                preFormataffectedOldPathMinutes = affectedOldPath[-1][3] # The time taken to get to the last station on the path, which is stored as the fourth element [prevStation, currStation, LineUsed, TimeToStation]
                oldPathTime, oldPathArrival = processTime(preFormataffectedOldPathMinutes, time)
                formattedOldPath = formatPathData(affectedOldPath, affectedOldPathDesriptions, start, databaseFile)

                # New Path (Optimised)
                newPath = resultsObject.newPath
                newPathDescriptions = resultsObject.newPathDescriptions
                preFormataffectedNewPathMinutes = newPath[-1][3] # The time taken to get to the last station on the path, which is stored as the fourth element [prevStation, currStation, LineUsed, TimeToStation]
                newPathTime, newPathArrival = processTime(preFormataffectedNewPathMinutes, time)
                formattedNewPath = formatPathData(newPath, newPathDescriptions, start, databaseFile)

    return render_template(
        "mainPage.html",
        error=error,
        startLines=startStationLines,
        endLines=endStationLines,
        formattedOldPath=formattedOldPath,
        formattedNewPath=formattedNewPath,
        oldPathTime=oldPathTime,
        oldPathArrival=oldPathArrival,
        newPathTime=newPathTime,
        newPathArrival=newPathArrival
    )


# Update User Parameters Page
@app.route('/update', methods=['GET', 'POST'])
def updatePage():
    """
    Displays and allows updating of user-specific parameters.
    """

    databaseFile = app.config["DATABASE_FILE"]
    username = session["username"]

    # Retrieve user parameters from database
    connection = sqlite3.connect(databaseFile)
    cursor = connection.cursor()
    cursor.execute("""
        SELECT 
            CHANGING_TIME, 
            MAX_TIME_WINDOW, 
            rawArrivalPeakOffset, 
            rawDeparturePeakOffset,
            ATTENDANCE, 
            TRAIN_PROPORTION, 
            SIGMA_FACTOR, 
            MINIMUM_PEOPLE, 
            PERSON_DELAY,
            PROPAGATION_FACTOR, 
            WALKING_TIME, 
            WALKING_SPEED, 
            NORMAL, 
            SLIGHTLY, 
            BUSY
        FROM Users
        WHERE Username = ?
    """, (username,))
    userData = cursor.fetchone()
    connection.close()

    # Unpack values for template
    (CHANGING_TIME,
     MAX_TIME_WINDOW,
     rawArrivalPeakOffset,
     rawDeparturePeakOffset,
     ATTENDANCE,
     TRAIN_PROPORTION,
     SIGMA_FACTOR,
     MINIMUM_PEOPLE,
     PERSON_DELAY,
     PROPAGATION_FACTOR,
     WALKING_TIME,
     WALKING_SPEED,
     NORMAL,
     SLIGHTLY,
     BUSY) = userData

    return render_template("updatePage.html",
                           CHANGING_TIME=CHANGING_TIME,
                           MAX_TIME_WINDOW=MAX_TIME_WINDOW,
                           rawArrivalPeakOffset=rawArrivalPeakOffset,
                           rawDeparturePeakOffset=rawDeparturePeakOffset,
                           ATTENDANCE=ATTENDANCE,
                           TRAIN_PROPORTION=TRAIN_PROPORTION,
                           SIGMA_FACTOR=SIGMA_FACTOR,
                           MINIMUM_PEOPLE=MINIMUM_PEOPLE,
                           PERSON_DELAY=PERSON_DELAY,
                           PROPAGATION_FACTOR=PROPAGATION_FACTOR,
                           WALKING_TIME=WALKING_TIME,
                           WALKING_SPEED=WALKING_SPEED,
                           NORMAL=NORMAL,
                           SLIGHTLY=SLIGHTLY,
                           BUSY=BUSY)


# Database Error Page
@app.route("/db_error")
def databaseError():
    """
    Displays a database error page.
    """
    flagsFile = app.config["FLAGS_FILE"]

    with open(flagsFile, "r") as f:
        data = json.load(f)
        errorMessage = data["error"]

    return render_template("databaseError.html") # Can add error message in future


# Database Creation Function
def createDatabase():
    """
    Creates the database using databaseCreation.main().
    Writes success/failure status to flags file.
    """
    databaseFile = app.config["DATABASE_FILE"]
    LinesjsonFile = app.config["LINES_JSON_FILE"]
    TfL_API_KEY = app.config["TFL_API_KEY"]
    OPENCAGE_API_KEY = app.config["OPENCAGE_API_KEY"]
    londonjsonFile = app.config["LONDONJSON_FILE"]
    leaguesjsonFile = app.config["LEAGUES_JSON_FILE"]
    flagsFile = app.config["FLAGS_FILE"]
    defaultParametersFile = app.config["DEFAULT_PARAMETERS_FILE"]

    message = databaseCreation.main(databaseFile, LinesjsonFile, TfL_API_KEY, OPENCAGE_API_KEY, londonjsonFile, leaguesjsonFile, defaultParametersFile)

    if message == "success":
        status = "success"
    else:
        # Remove database if creation failed
        status = "failed"
        databaseFile = Path(app.config["DATABASE_FILE"])
        if databaseFile.exists():
            databaseFile.unlink()

    # Write status to flags file
    data = {
        "status": status,
        "error": message
    }

    with open(flagsFile, "w") as file:
        json.dump(data, file)

    print("Database created")


# Format Duration
def formatDuration(minutes):
    """
    Converts minutes into hours and minutes string.
    """

    hours = round(minutes // 60)
    minutesLeft = round(minutes % 60)

    if hours > 0:
        return f"{hours} hours and {minutesLeft} minutes"
    else:
        return f"{minutesLeft} minutes"


# Process Time
def processTime(totalUnprocessedTime, timeOfJourney):
    """
    Calculates journey duration and arrival time.
    """
    startTime = datetime.strptime(timeOfJourney, "%H:%M")
    journeyTimeObject = timedelta(minutes=round(totalUnprocessedTime))
    arrivalTime = startTime + journeyTimeObject
    arrivalTimeString = arrivalTime.strftime("%H:%M")
    duration = formatDuration(totalUnprocessedTime)
    return duration, arrivalTimeString


# Format Path Data Helper
def formatPathData(affectedPath, affectedPathDesriptions, startStation, databaseFile):
    """
    Converts path tuples into classes.mainPagePathClass objects for display.
    Adds line names, station names, and descriptions.
    """
    connection = sqlite3.connect(databaseFile)
    cursor = connection.cursor()

    # Get starting station NaPTAN
    cursor.execute("""
        SELECT NaPTAN
        FROM Stations
        WHERE StationName = ?
        """, (startStation,))
    startStationNaPTAN = cursor.fetchall()[0][0]

    returnAffectedPath = []

    # Initialise first path object
    firstConnection = affectedPath[0]
    firstLine = firstConnection[2]
    currentObject = classes.mainPagePathClass(firstLine)
    currentObject.addStation(startStationNaPTAN)

    # Iterate through affectedPath connections
    for connectionTuple in affectedPath:
        previous, currentStation, line, distance = connectionTuple

        if line == currentObject.LineID:
            currentStation = connectionTuple[1]
            currentObject.addStation(currentStation)
        else:
            returnAffectedPath.append(currentObject)
            currentObject = classes.mainPagePathClass(line)
            currentObject.addStation(currentStation)

    # Append last path object
    returnAffectedPath.append(currentObject)

    # Add names and descriptions
    for object in returnAffectedPath:
        object.getLineName(databaseFile)
        object.getStationNames(databaseFile)
        object.getDescription(affectedPathDesriptions)

    connection.close()
    return returnAffectedPath


def getLines(stationName, databaseFile):
    """
    Returns a list of lines a station belongs to.
    """
    connection = sqlite3.connect(databaseFile)
    cursor = connection.cursor()

    cursor.execute("""
        SELECT Lines.LineName
        FROM Lines
        JOIN StationLineRelationships
            ON Lines.LineID = StationLineRelationships.LineID
        JOIN Stations
            ON StationLineRelationships.NaPTAN = Stations.NaPTAN
        WHERE Stations.StationName = ?
        ORDER BY Lines.LineName
        """, (stationName,))

    results = cursor.fetchall()

    connection.close()

    returnList = [resultTuple[0] for resultTuple in results]

    return returnList


# Background Database Update
def backgroundDataFetch():
    """
    Updates the database in the background while preserving user data.
    """
    databaseFile = app.config["DATABASE_FILE"]

    connection = sqlite3.connect(databaseFile)
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM Users")
    users_data = cursor.fetchall()  # List of tuples with all user rows
    connection.close()

    # Delete old database
    databasePath = Path(databaseFile)
    databasePath.unlink()

    # Recreate database
    createDatabase()

    # Restore user data
    if users_data:
        connection = sqlite3.connect(databaseFile)
        cursor = connection.cursor()
        cursor.executemany("""
                INSERT OR REPLACE INTO Users (
                    Username, 
                    PasswordHash,
                    Salt, 
                    CHANGING_TIME, 
                    MAX_TIME_WINDOW, 
                    rawArrivalPeakOffset, 
                    rawDeparturePeakOffset,
                    ATTENDANCE, 
                    TRAIN_PROPORTION, 
                    SIGMA_FACTOR, 
                    MINIMUM_PEOPLE, 
                    PERSON_DELAY,
                    PROPAGATION_FACTOR, 
                    WALKING_TIME, 
                    WALKING_SPEED, 
                    NORMAL, 
                    SLIGHTLY, 
                    BUSY
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, users_data)
        connection.commit()
        connection.close()


# Route to Trigger Background Database Fetch
@app.route("/fetch_new_data", methods=["POST"])
def fetchNewData():
    threading.Thread(target=backgroundDataFetch).start()
    return redirect(url_for("loadPage"))


# Save User Parameters
@app.route("/save_parameters", methods=["POST"])
def saveParameters():
    """
    Saves user-modified parameters and updates stadium data.
    """
    databaseFile = app.config["DATABASE_FILE"]
    londonjsonFile = app.config["LONDONJSON_FILE"]

    username = session.get("username")
    data = request.get_json()

    values = (
        float(data["CHANGING_TIME"]),
        float(data["MAX_TIME_WINDOW"]),
        float(data["rawArrivalPeakOffset"]),
        float(data["rawDeparturePeakOffset"]),
        float(data["ATTENDANCE"]),
        float(data["TRAIN_PROPORTION"]),
        float(data["SIGMA_FACTOR"]),
        float(data["MINIMUM_PEOPLE"]),
        float(data["PERSON_DELAY"]),
        float(data["PROPAGATION_FACTOR"]),
        float(data["WALKING_TIME"]),
        float(data["WALKING_SPEED"]),
        float(data["NORMAL"]),
        float(data["SLIGHTLY"]),
        float(data["BUSY"]),
        username  # WHERE clause
    )

    connection = sqlite3.connect(databaseFile)
    cursor = connection.cursor()
    cursor.execute("""
        UPDATE Users SET
            CHANGING_TIME = ?,
            MAX_TIME_WINDOW = ?,
            rawArrivalPeakOffset = ?,
            rawDeparturePeakOffset = ?,
            ATTENDANCE = ?,
            TRAIN_PROPORTION = ?,
            SIGMA_FACTOR = ?,
            MINIMUM_PEOPLE = ?,
            PERSON_DELAY = ?,
            PROPAGATION_FACTOR = ?,
            WALKING_TIME = ?,
            WALKING_SPEED = ?,
            NORMAL = ?,
            SLIGHTLY = ?,
            BUSY = ?
        WHERE Username = ?
        """, values)
    connection.commit()
    connection.close()

    # Recalculate stadium data
    walkingTime = float(data["WALKING_TIME"])
    walkingSpeed = float(data["WALKING_SPEED"])

    storeStadiumData.redoStore(walkingTime, walkingSpeed, londonjsonFile, databaseFile)

    return jsonify({"success": True})


# Logout
@app.route("/logout", methods=["POST"])
def logout():
    """
    Logs out the user by removing session.
    """
    session.pop("username", None)  # Remove username from session
    return redirect(url_for("loginPage"))


# Load Default Parameters
@app.route("/load_default_parameters", methods=["GET"])
def loadDefaultParameters():
    defaultParametersFile = app.config["DEFAULT_PARAMETERS_FILE"]

    with open(defaultParametersFile, "r") as file:
        data = json.load(file)
    return jsonify(data)


# Flags Management
@app.route("/updateFlags", methods=["POST"])
def updateFlags():
    """
    Updates flags file when database creation starts.
    """
    flagsFile = app.config["FLAGS_FILE"]

    data = {
        "status": "creating",
        "error": "success"
    }

    with open(flagsFile, "w") as file:
        json.dump(data, file)
    return jsonify({"success": True})


@app.route('/check_flag', methods=['GET'])
def checkFlag():
    """
    Returns current flags status (database creation, error, previous page).
    """
    flagsFile = app.config["FLAGS_FILE"]

    response = {
        "status": "creating",
        "error": None,
        "previousPage": session.get("previousPage")
    }

    try:
        with open(flagsFile, "r") as file:
            response.update(json.load(file))
    except:
        pass

    return jsonify(response)


# Autocomplete Station Search
@app.route("/get_stations")
def get_stations():
    """
    Returns station suggestions for autocomplete.
    """
    databaseFile = app.config["DATABASE_FILE"]
    searchTerm = request.args.get("search", "")

    connection = sqlite3.connect(databaseFile)
    cursor = connection.cursor()

    cursor.execute("""
        SELECT StationName
        FROM Stations
        WHERE StationName LIKE ?
        ORDER BY StationName
        LIMIT 20
    """, (f"%{searchTerm}%",))

    rows = cursor.fetchall()
    connection.close()

    results = [
        {"id": StationName, "text": StationName}
        for StationName in rows
    ]

    returnJson = jsonify(results)
    return returnJson


# Call the programme
if __name__ == '__main__':
    databaseFile = "data/te st.db"
    LinesjsonFile = "lines.json"
    TfL_API_KEY = "0ff5a2076cd640cb957e63d6947efc61"
    OPENCAGE_API_KEY = "eb0e2c9b71cc45f7aafe0ae4ecc44cc2"
    londonjsonFile = "londonClubs.json"
    leaguesjsonFile = "leagues.json"
    flagFile = "data/flags.json"
    defaultParametersFile = "defaultParameters.json"
    setUpConfig(app, databaseFile, LinesjsonFile, TfL_API_KEY, OPENCAGE_API_KEY, londonjsonFile, leaguesjsonFile, flagFile, defaultParametersFile)
    app.run()