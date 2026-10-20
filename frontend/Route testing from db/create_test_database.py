import sqlite3
from pathlib import Path

db_path = Path(__file__).with_name("test_navigation.db")  # Path to the SQLite database file

connection = sqlite3.connect(db_path) # Create a connection to the SQLite database
cursor = connection.cursor() #Cusor for executing SQL commands

cursor.execute("""
CREATE TABLE IF NOT EXISTS locations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL
)
""")
#cities of Camden county with Lats and longs, with a few others for testing purposes
locations = [
    ("Audubon, NJ", 39.8837, -75.0682),
    ("Barrington, NJ", 39.8590, -75.0560),
    ("Bellmawr, NJ", 39.8634, -75.0932),
    ("Berlin, NJ", 39.7901, -74.9271),
    ("Camden, NJ", 39.9259, -75.1196),
    ("Cherry Hill, NJ", 39.9268, -75.0240),
    ("Chesilhurst, NJ", 39.7323, -74.8810),
    ("Clementon, NJ", 39.7951, -75.0118),
    ("Collingswood, NJ", 39.9140, -75.0706),
    ("Gibbsboro, NJ", 39.8340, -74.9929),
    ("Gloucester City, NJ", 39.9015, -75.1326),
    ("Gloucester Township, NJ", 39.7890, -75.0740),
    ("Haddonfield, NJ", 39.8850, -75.0120),
    ("Haddon Heights, NJ", 39.8690, -75.0732),
    ("Hi-Nella, NJ", 39.8329, -75.0179),
    ("Laurel Springs, NJ", 39.8137, -75.0132),
    ("Lawnside, NJ", 39.8601, -75.0426),
    ("Magnolia, NJ", 39.8546, -75.0391),
    ("Merchantville, NJ", 39.9540, -75.0440),
    ("Mount Ephraim, NJ", 39.8730, -75.0832),
    ("Oaklyn, NJ", 39.8945, -75.0790),
    ("Pennsauken Township, NJ", 39.9570, -75.0640),
    ("Pine Hill, NJ", 39.7845, -74.9990),
    ("Runnemede, NJ", 39.8451, -75.0770),
    ("Somerdale, NJ", 39.8340, -75.0390),
    ("Stratford, NJ", 39.8348, -75.0210),
    ("Tavistock, NJ", 39.8780, -75.0390),
    ("Voorhees Township, NJ", 39.8437, -75.0240),
    ("Waterford Township, NJ", 39.7322, -74.8011),
    ("Winslow Township, NJ", 39.7289, -74.9450),
    ("Woodlyne, NJ", 39.9230, -75.1012),
    ("Philadelphia, PA", 39.9526, -75.1652),
    ("Trenton, NJ", 40.2171, -74.7429),
]

for name, latitude, longitude in locations: #update the database with the locations, if they don't exist, insert them
    cursor.execute(
        "UPDATE locations SET latitude = ?, longitude = ? WHERE name = ?",
        (latitude, longitude, name),
    )
    if cursor.rowcount == 0:
        cursor.execute(
            "INSERT INTO locations (name, latitude, longitude) VALUES (?, ?, ?)",
            (name, latitude, longitude),
        )

connection.commit()
connection.close() #make sure to close the connection to the database after committing the changes

print("Navi-Gator database created successfully!")