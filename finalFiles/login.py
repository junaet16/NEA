import json
import hashlib
import os
import sqlite3
import classes

# Generates a cryptographically secure random salt
# A unique salt is used per user to protect against rainbow table attacks
def generateSalt():
    return os.urandom(16).hex() #Creates a random 16-byte salt and returns it as hex


# Creates a SHA-256 hash of the password combined with a salt
# Passwords are never stored in plain text
def createHashPassword(password, salt):
    saltedPassword = salt + password
    byteForm = saltedPassword.encode()
    hashObject = hashlib.sha256(byteForm)
    hashedPassword = hashObject.hexdigest()
    return hashedPassword


# Creates a new user account and stores default modelling parameters
# Each user begins with a copy of the default assumptions, which they can later modify
def createAccount(defaultParametersFile, username, password, databaseFile):
    salt = generateSalt()
    hashedPassword = createHashPassword(password, salt)

    # Loads default crowding and delay parameters from a file storing default values
    defaultParametersObject = classes.AccountCreationParameters(defaultParametersFile)

    # Tuple contains login credentials and all model parameters
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
        # Insert user credentials and modelling parameters into Users table
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
        # Likely occurs if username already exists
        accountMade = False

    connection.commit()
    connection.close()

    return accountMade


# Authenticates a user by hashing the entered password with the stored salt
def login(databaseFile, username, password):
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
            message = "Login Successful"
        else:
            message = "Wrong Password"
    else:
        message = "Account Not Found"

    connection.close()
    return message


# For testing purposes
def main(username, password, defaultParametersFile, databaseFile):
    accountCreated = createAccount(defaultParametersFile, username, password, databaseFile)
    loginSuccessful = login(databaseFile, username, password)
    print(accountCreated)
    print(loginSuccessful)


#For testing purposes
if __name__ == '__main__':
    username = "Jun8"
    password = "h"
    defaultParametersFile = "defaultParameters.json"
    databaseFile = "test.db"
    main(username, password, defaultParametersFile, databaseFile)