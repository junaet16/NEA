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


app = Flask(__name__)
app.secret_key = "VERY_SECRET_KEY"


def setUpConfig(app, databaseFile, LinesjsonFile, TfL_API_KEY, OPENCAGE_API_KEY, londonjsonFile, leaguesjsonFile, flagsFile, defaultParametersFile):
    app.config["DATABASE_FILE"] = databaseFile
    app.config["LINES_JSON_FILE"] = LinesjsonFile
    app.config["TFL_API_KEY"] = TfL_API_KEY
    app.config["OPENCAGE_API_KEY"] = OPENCAGE_API_KEY
    app.config["LONDONJSON_FILE"] = londonjsonFile
    app.config["LEAGUES_JSON_FILE"] = leaguesjsonFile
    app.config["FLAGS_FILE"] = flagsFile
    app.config["DEFAULT_PARAMETERS_FILE"] = defaultParametersFile


@app.route('/', methods=['GET', 'POST']) #Need to finish account creation
def loginPage():
    databaseFile = app.config["DATABASE_FILE"]
    flagsFile = app.config["FLAGS_FILE"]
    defaultParametersFile = app.config["DEFAULT_PARAMETERS_FILE"]
    message = None

    session["previousPage"] = request.url

    databaseFilePath = Path(databaseFile)
    if not databaseFilePath.exists():
        flagsPath = Path(flagsFile)

        if not flagsPath.exists():
            with open(flagsFile, "w") as file:
                json.dump({"databaseCreated": False}, file)

        threading.Thread(target=createDatabase).start()
        return redirect(url_for("loadPage"))

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


@app.route('/load', methods=['GET', 'POST'])
def loadPage():
    return render_template("loading.html")


@app.route('/main', methods=['GET', 'POST']) #Need to uncomment out the validation for correct time
def mainPage():
    if "username" not in session:
        return redirect(url_for("loginPage"))

    databaseFile = app.config["DATABASE_FILE"]
    username = session["username"]

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
            return redirect(url_for("updatePage"))
        else:
            start = request.form.get('start')
            end = request.form.get('end')
            date = request.form.get('date')
            time = request.form.get('time')
            selectedTime = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")

            if start == end:
                error = "Start and end stations must be different"
            #ADD ELIF STATEMENT HERE
            else:
                dateObject = datetime.strptime(date, "%Y-%m-%d")
                passInDate = dateObject.strftime("%d/%m/%Y")

                startStationLines = getLines(start, databaseFile)
                endStationLines = getLines(end, databaseFile)

                resultsObject = getResults.main(passInDate, time, start, end, databaseFile, username)

                affectedOldPath = resultsObject.affectedOldPath
                affectedOldPathDesriptions = resultsObject.affectedOldPathDesriptions
                preFormataffectedOldPathMinutes = affectedOldPath[-1][3]
                oldPathTime, oldPathArrival = processTime(preFormataffectedOldPathMinutes, time)
                formattedOldPath = formatPathData(affectedOldPath, affectedOldPathDesriptions, start, databaseFile)

                newPath = resultsObject.newPath
                newPathDescriptions = resultsObject.newPathDescriptions
                preFormataffectedNewPathMinutes = newPath[-1][3]
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


@app.route('/update', methods=['GET', 'POST'])
def updatePage():
    databaseFile = app.config["DATABASE_FILE"]
    username = session["username"]

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


def createDatabase():
    databaseFile = app.config["DATABASE_FILE"]
    LinesjsonFile = app.config["LINES_JSON_FILE"]
    TfL_API_KEY = app.config["TFL_API_KEY"]
    OPENCAGE_API_KEY = app.config["OPENCAGE_API_KEY"]
    londonjsonFile = app.config["LONDONJSON_FILE"]
    leaguesjsonFile = app.config["LEAGUES_JSON_FILE"]
    flagsFile = app.config["FLAGS_FILE"]
    defaultParametersFile = app.config["DEFAULT_PARAMETERS_FILE"]

    databaseCreation.main(databaseFile, LinesjsonFile, TfL_API_KEY, OPENCAGE_API_KEY, londonjsonFile, leaguesjsonFile, defaultParametersFile)

    with open(flagsFile, "w") as file:
        json.dump({"databaseCreated": True}, file)

    print("Database created")


def formatDuration(minutes):
    hours = round(minutes // 60)
    minutesLeft = round(minutes % 60)

    if hours > 0:
        return f"{hours} hours and {minutesLeft} minutes"
    else:
        return f"{minutesLeft} minutes"


def processTime(totalUnprocessedTime, timeOfJourney):
    startTime = datetime.strptime(timeOfJourney, "%H:%M")
    journeyTimeObject = timedelta(minutes=round(totalUnprocessedTime))
    arrivalTime = startTime + journeyTimeObject
    arrivalTimeString = arrivalTime.strftime("%H:%M")
    duration = formatDuration(totalUnprocessedTime)
    return duration, arrivalTimeString


def formatPathData(affectedPath, affectedPathDesriptions, startStation, databaseFile):
    connection = sqlite3.connect(databaseFile)
    cursor = connection.cursor()

    cursor.execute("""
        SELECT NaPTAN
        FROM Stations
        WHERE StationName = ?
        """, (startStation,))
    startStationNaPTAN = cursor.fetchall()[0][0]

    returnAffectedPath = []

    firstConnection = affectedPath[0]
    firstLine = firstConnection[2]
    currentObject = classes.mainPagePathClass(firstLine)
    currentObject.addStation(startStationNaPTAN)

    for connectionTuple in affectedPath:
        previous, currentStation, line, distance = connectionTuple

        if line == currentObject.LineID:
            currentStation = connectionTuple[1]
            currentObject.addStation(currentStation)
        else:
            returnAffectedPath.append(currentObject)
            currentObject = classes.mainPagePathClass(line)
            currentObject.addStation(currentStation)

    returnAffectedPath.append(currentObject)

    for object in returnAffectedPath:
        object.getLineName(databaseFile)
        object.getStationNames(databaseFile)
        object.getDescription(affectedPathDesriptions)

    connection.close()
    return returnAffectedPath


def getLines(stationName, databaseFile):
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


@app.route('/check_flag', methods=['GET'])
def checkFlag():
    flagsFile = app.config["FLAGS_FILE"]
    try:
        with open(flagsFile, "r") as flag_file:
            flags = json.load(flag_file)
            flag = flags.get("databaseCreated")
    except:
        flag = False

    with open(flagsFile, "w") as flag_file:
        pass #Wipe

    return jsonify({
        "databaseCreated": flag,
        "previousPage": session.get("previousPage")
    })


@app.route("/get_stations")
def get_stations():
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