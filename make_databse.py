import sqlite3

connection = sqlite3.connect("nea.db")

cursor = connection.cursor()

cursor.executescript("""
CREATE TABLE IF NOT EXISTS stations (
    station_id TEXT PRIMARY KEY,
    station_name TEXT,
    lat REAL,
    lon REAL,
    travel_zone INTEGER
);

CREATE TABLE IF NOT EXISTS lines(
    line_id TEXT PRIMARY KEY,
    line_name TEXT,
    colour TEXT)
    """)

connection.commit()
connection.close()