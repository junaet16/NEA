import json
import hashlib
import os
import sqlite3


def generateSalt():
    return os.urandom(16).hex() #Creates a random 16-byte salt and returns it as hex


def createHashPassword(password, salt):
    saltedPassword = salt + password
    byteForm = saltedPassword.encode()
    hashObject = hashlib.sha256(byteForm)
    hashedPassword = hashObject.hexdigest()
    return hashedPassword


def createAccount(defaultParametersFile, username, password):
    salt = generateSalt()
    hashedPassword = createHashPassword(password, salt)
    print(hashedPassword)
    #Finish storing


def login(defaultParametersFile, username, password):
    pass


def main(username, password, defaultParametersFile):
    createAccount(defaultParametersFile, username, password)


if __name__ == '__main__':
    username = "Junaet"
    password = "hello123"
    defaultParametersFile = "defaultParameters.json"
    databaseFile = "final.db"
    main(username, password, defaultParametersFile)