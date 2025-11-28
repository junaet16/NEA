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
    parametersDictionary = defaultParametersObject.megaDictionary

    connection = sqlite3.connect(databaseFile)
    cursor = connection.cursor()

    try:
        cursor.execute("""
            INSERT INTO Users (
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
                WALKING_SPEED
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                       (username,
                        hashedPassword,
                        salt,
                        parametersDictionary["CHANGING_TIME"],
                        parametersDictionary["MAX_TIME_WINDOW"],
                        parametersDictionary["rawArrivalPeakOffset"],
                        parametersDictionary["rawDeparturePeakOffset"],
                        parametersDictionary["ATTENDANCE"],
                        parametersDictionary["TRAIN_PROPORTION"],
                        parametersDictionary["SIGMA_FACTOR"],
                        parametersDictionary["MINIMUM_PEOPLE"],
                        parametersDictionary["PERSON_DELAY"],
                        parametersDictionary["PROPAGATION_FACTOR"],
                        parametersDictionary["WALKING_TIME"],
                        parametersDictionary["WALKING_SPEED"])
                       )
        connection.commit()
        connection.close()
        accountMade = True
    except:
        accountMade = False


def login(defaultParametersFile, username, password):
    pass


def main(username, password, defaultParametersFile, databaseFile):
    createAccount(defaultParametersFile, username, password, databaseFile)


if __name__ == '__main__':
    username = "Junaet"
    password = "hello123"
    defaultParametersFile = "defaultParameters.json"
    databaseFile = "final.db"
    main(username, password, defaultParametersFile, databaseFile)