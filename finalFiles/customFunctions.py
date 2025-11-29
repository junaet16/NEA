import requests
import time
import sqlite3
import classes


def safeGet(url, params=None):
    waitTime = 65
    attempts = 3
    for attempt in range(attempts):
        try:
            response = requests.get(url, params=params, timeout=5)

            if response.status_code == 429:
                print(f"Rate limit reached: Attempt {attempt + 1} of {attempts}")
                time.sleep(waitTime)
                continue

            if response.status_code >= 500 and response.status_code < 600:
                print(f"Server error: Attempt {attempt + 1} of 2")
                time.sleep(waitTime)
                continue

            return response
        except:
            pass


#Creates a parameter object to store the parameters used for calculation
def getParameters(username, databaseFile):
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

    result = cursor.fetchall()[0]
    connection.close()

    (
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
    ) = result

    parameterObject = classes.Parameters(
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
    )

    parameterObject.calculateWindow()
    parameterObject.calculatePeakOffset()
    parameterObject.calculateMinutesOffset()

    return parameterObject