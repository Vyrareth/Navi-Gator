import sqlite3
from pathlib import Path

db_path = Path(__file__).with_name("navigation.db")  # Path to the SQLite database file

connection = sqlite3.connect(db_path)
cursor = connection.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS locations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL
)
""")

cursor.execute("SELECT COUNT(*) FROM locations")

if cursor.fetchone()[0] == 0:
    cursor.executemany(
        "INSERT INTO locations (name, latitude, longitude) VALUES (?, ?, ?)",
        [
            ("Camden, NJ", 39.9259, -75.1196),
            ("Philadelphia, PA", 39.9526, -75.1652),
            ("Trenton, NJ" , 40.2171, -74.7429),
        ]
    )

connection.commit()
connection.close()

print("Navi-Gator database created successfully!")