from flask import Flask, jsonify, render_template
import sqlite3
from pathlib import Path

app = Flask(__name__) #using flask to create a web application for routing and navigation

def get_db_connection(): #function used to connect to the SQLite database
    db_path = Path(__file__).with_name("test_navigation.db")
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    return connection

@app.route("/") 
def home():
    connection = get_db_connection()
    locations = connection.execute("SELECT * FROM locations").fetchall()
    connection.close()

    return render_template("routing_index.html", locations=locations) #

@app.route("/locations")
def get_locations():
    connection = get_db_connection()

    try:
        locations = connection.execute(
            "SELECT * FROM locations"
            ).fetchall()
        
        return jsonify([dict(location) for location in locations])
    finally:
        connection.close()

if __name__ == "__main__":
    app.run(debug=True)