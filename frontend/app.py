from flask import Flask, jsonify, render_template
import sqlite3
from pathlib import Path

app = Flask(__name__)

def get_db_connection():
    db_path = Path(__file__).with_name("naviGator_camcountyUpdated_db.db")
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    return connection

@app.route("/")
def home():
    connection = get_db_connection()
    locations = connection.execute("SELECT * FROM Road").fetchall()
    connection.close()

    return render_template("index.html", locations=locations)

@app.route("/locations")
def get_locations():
    connection = get_db_connection()

    try:
        locations = connection.execute(
            "SELECT * FROM Road"
            ).fetchall()
        
        return jsonify([dict(location) for location in locations])
    finally:
        connection.close()

@app.route("/roads")
def get_roads():
    connection = get_camden_connection()

    try:
        roads = connection.execute(
            "SELECT RoadID, Road_Name FROM Road LIMIT 100"
        ).fetchall()

        return jsonify([dict(road) for road in roads])
    
    finally:
        connection.close()

@app.route("/segments")
def get_segments():
    connection = get_db_connection()

    try:
        segments = connection.execute("""
            SELECT
                Segments.SegmentID,
                Segments.RoadID,
                Road.Road_Name,
                Segments.Photo_File
            FROM Segments
            JOIN Road ON Segments.RoadID = Road.RoadID
            LIMIT 100
        """).fetchall()

        return jsonify([dict(segment) for segment in segments])
    
    finally:
        connection.close()

if __name__ == "__main__":
    app.run(debug=True)