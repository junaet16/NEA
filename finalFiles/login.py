import json
import hashlib
import os
import sqlite3
import classes


def generateSalt():
    return os.urandom(16).hex() #Creates a random 16-byte salt and returns it as hex


def createHashPassword(password, salt):
    saltedPassword = salt + password
    byteForm = saltedPassword.encode()
    hashObject = hashlib.sha256(byteForm)
    hashedPassword = hashObject.hexdigest()
    return hashedPassword


def createAccount(defaultParametersFile, username, password, databaseFile):
    salt = generateSalt()
    hashedPassword = createHashPassword(password, salt)
    defaultParametersObject = classes.AccountCreationParameters(defaultParametersFile)

    parameterTuple = (
        username,
        hashedPassword,
        salt,
        defaultParametersObject.CHANGING_TIME,
        defaultParametersObject.MAX_TIME_WINDOW,
        defaultParametersObject.rawArrivalPeakOffset,
        defaultParametersObject.rawDeparturePeakOffset,
        defaultParametersObject.ATTENDANCE,
        defaultParametersObject.TRAIN_PROPORTION,
        defaultParametersObject.SIGMA_FACTOR,
        defaultParametersObject.MINIMUM_PEOPLE,
        defaultParametersObject.PERSON_DELAY,
        defaultParametersObject.PROPAGATION_FACTOR,
        defaultParametersObject.WALKING_TIME,
        defaultParametersObject.WALKING_SPEED,
        defaultParametersObject.NORMAL,
        defaultParametersObject.SLIGHTLY,
        defaultParametersObject.BUSY
    )

    connection = sqlite3.connect(databaseFile)
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO Users(
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
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            parameterTuple
        )
        accountMade = True
    except:
        accountMade = False

    connection.commit()
    connection.close()

    return accountMade


def login(databaseFile, username, password):
    message = None
    connection = sqlite3.connect(databaseFile)
    cursor = connection.cursor()

    cursor.execute("""
        SELECT PasswordHash, Salt
        FROM Users
        WHERE Username = ?
    """, (username,))

    try:
        result = cursor.fetchall()[0]
        accountFound = True
    except:
        accountFound = False

    if accountFound:
        storedHash, storedSalt = result
        loginHash = createHashPassword(password, storedSalt)

        if loginHash == storedHash:
            loginSuccessful = True
            message = "Login Successful"
        else:
            loginSuccessful = False
            message = "Wrong Password"
    else:
        message = "Account Not Found"
    return message


def main(username, password, defaultParametersFile, databaseFile):
    accountCreated = createAccount(defaultParametersFile, username, password, databaseFile)
    loginSuccessful = login(databaseFile, username, password)
    print(accountCreated)
    print(loginSuccessful)


if __name__ == '__main__':
    username = "Jun8"
    password = "h"
    defaultParametersFile = "defaultParameters.json"
    databaseFile = "test.db"
    main(username, password, defaultParametersFile, databaseFile)