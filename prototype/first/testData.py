import sqlite3


def CreateTestDatabase(databaseFile):
    connection = sqlite3.connect(databaseFile)
    cursor = connection.cursor()

    # Create Connections table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS connections (
        StationA TEXT,
        StationB TEXT,
        LineID TEXT,
        BaseTravelTime INTEGER
    )
    """)

    # Clear old data (for repeated testing)
    cursor.execute("DELETE FROM connections")

    # Fake test data

    testConnections = [
        # Path 1: A->B->C (2 lines)
        ("A", "B", "Line1", 4),
        ("B", "C", "Line2", 5),
        # Path 2: A->D->C (1 line)
        ("A", "D", "Line3", 5),
        ("D", "C", "Line3", 5),
        # Reverse directions
        ("B", "A", "Line1", 5),
        ("C", "B", "Line2", 5),
        ("D", "A", "Line3", 5),
        ("C", "D", "Line3", 5),
    ]


    cursor.executemany("""
    INSERT INTO connections (StationA, StationB, LineID, BaseTravelTime)
    VALUES (?, ?, ?, ?)
    """, testConnections)

    connection.commit()
    connection.close()


if __name__ == "__main__":
    CreateTestDatabase("test.db")