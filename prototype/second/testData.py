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
    # Network layout (simplified):

    #
    # A --(Red)--> B --(Red)--> C
    #  \                        | (Blue)
    #   \(Blue)--> D --(Blue)--> E
    #                 \
    #                 (Green)
    #                   \
    #                    C
    #

    testConnections = [
        ("A", "B", "Red", 5),
        ("B", "C", "Red", 5),

        ("A", "D", "Blue", 4),
        ("D", "E", "Blue", 4),
        ("E", "C", "Blue", 4),

        ("D", "C", "Green", 6),

        # Add reverse directions (for realistic networks)
        ("B", "A", "Red", 5),
        ("C", "B", "Red", 5),

        ("D", "A", "Blue", 4),
        ("E", "D", "Blue", 4),
        ("C", "E", "Blue", 4),

        ("C", "D", "Green", 6),
    ]

    cursor.executemany("""
    INSERT INTO connections (StationA, StationB, LineID, BaseTravelTime)
    VALUES (?, ?, ?, ?)
    """, testConnections)

    connection.commit()
    connection.close()


if __name__ == "__main__":
    CreateTestDatabase("test.db")