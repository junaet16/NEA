import requests
import time
import sqlite3
import classes


# Performs a safe HTTP GET request with retry logic
# Handles rate limiting, server errors, and lack of internet connection
def safeGet(url, params=None):
    waitTime = 65 # Wait time in seconds when rate-limited or server error occurs
    attempts = 3 # Maximum number of retry attempts
    for attempt in range(attempts):
        try:
            response = requests.get(url, params=params, timeout=5)

            # Handle API rate limiting
            if response.status_code == 429:
                print(f"Rate limit reached: Attempt {attempt + 1} of {attempts}")
                time.sleep(waitTime)
                continue

            # Handle server-side errors
            if response.status_code >= 500 and response.status_code < 600:
                print(f"Server error: Attempt {attempt + 1} of {attempts}")
                time.sleep(waitTime)
                continue

            # Successful or client-side response returned
            return response

        except:
            # Covers timeouts, connection errors, etc.
            pass

    # If all attempts fail, return the status code if available
    try:
        return response.status_code
    except:
        # Occurs if no response was ever received (e.g. no internet)
        return 0


def getParameters(username, databaseFile):
    # Creates a parameter object to store the parameters used for calculation
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

    # Creates a Parameters object which acts as a container for all assumptions
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

    # Compute values using the data just stored in the object, to be used later in the programme
    parameterObject.calculateWindow()
    parameterObject.calculatePeakOffset()
    parameterObject.calculateMinutesOffset()

    return parameterObject