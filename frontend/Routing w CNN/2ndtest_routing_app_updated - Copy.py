from flask import Flask, current_app, jsonify, render_template, request
from http.client import HTTPException
from json import JSONDecodeError
from queue import Queue
from threading import Lock, Thread
from typing import Any, Callable
from urllib.error import URLError
from urllib.request import urlopen
from uuid import uuid4
import importlib.util
import json
import math
import sqlite3
from pathlib import Path

app = Flask(__name__) #using flask to create a web application for routing and navigation
app.config["DATABASE"] = Path(__file__).with_name("test_navigation.db")

request_module_path = Path(__file__).with_name("Request - Copy.py")
request_module_spec = importlib.util.spec_from_file_location(
    "request_copy",
    request_module_path,
)
if request_module_spec is None or request_module_spec.loader is None:
    raise ImportError(f"Could not load route utilities from {request_module_path}.")
Request = importlib.util.module_from_spec(request_module_spec)
request_module_spec.loader.exec_module(Request)


def fetch_route( #function to fetch the route from the OSRM routing service
        #floating point numbers representing geographic coordinates
    start_longitude: float, 
    start_latitude: float,
    end_longitude: float,
    end_latitude: float,
) -> dict[str, Any] | None: #returns the route as a dictionary or None if no route is found
    coordinates = (
        f"{start_longitude},{start_latitude};{end_longitude},{end_latitude}" #format the coordinates as a string for the OSRM API
    )
    url = (
        "https://router.project-osrm.org/route/v1/driving/" #OSRM API endpoint for fetching driving routes
        f"{coordinates}?overview=full&geometries=geojson&steps=true"
    )

    with urlopen(url, timeout=15) as response: #send a request to the OSRM API with a timeout of 15 seconds
        data = json.loads(response.read()) #parse the JSON response from the OSRM API

    if not isinstance(data, dict): #check if the response is a dictionary
        raise ValueError("The routing service returned an invalid response.")
    routes = data.get("routes") #extract the list of routes from the response
    if data.get("code") != "Ok" or not isinstance(routes, list) or not routes: #check if the response is valid and contains routes
        return None

    route = routes[0] #take the first route from the list
    if not isinstance(route, dict): #check if the route is a dictionary
        raise ValueError("The routing service returned an invalid route.")
    geometry = route.get("geometry") #extract the geometry of the route
    distance = route.get("distance") #extract the distance of the route
    duration = route.get("duration") #extract the duration of the route
    legs = route.get("legs") #extract the legs of the route
    if (
        not isinstance(geometry, dict) #check if the geometry is a dictionary
        or not isinstance(distance, (int, float)) #check if the distance is a number
        or not isinstance(duration, (int, float)) #check if the duration is a number
        or not isinstance(legs, list) #check if the legs are a list
    ):
        raise ValueError("The routing service returned an incomplete route.")

    return { #returns the route as a dictionary containing geometry, distance, duration, and legs
        "geometry": geometry,
        "distance": distance,
        "duration": duration,
        "legs": legs,
    }

#class file for managing a queue of route requests
class RouteRequestQueue:
    def __init__(
        self,
        route_fetcher: Callable[ #function type for fetching routes
            [float, float, float, float], dict[str, Any] | None #takes four floats as input and returns a dictionary or None
        ] = fetch_route,
    ) -> None: #constructor for the RouteRequestQueue class
        self._jobs: dict[str, dict[str, Any]] = {} #dictionary to store job information
        self._queue: Queue[tuple[str, tuple[float, float, float, float]]] = Queue() #queue to store job IDs and their coordinates
        self._lock = Lock() #lock for thread-safe access to the jobs dictionary
        self._worker_started = False #flag to indicate if the worker thread has been started
        self._route_fetcher = route_fetcher #function to fetch routes

    def enqueue( #function to add a new route request to the queue
        self, coordinates: tuple[float, float, float, float] #coordinates of the route request
    ) -> str: #returns the job ID of the enqueued route request
        job_id = uuid4().hex #generate a unique job ID for the route request
        with self._lock: #acquire the lock to ensure thread-safe access to the jobs dictionary
            self._jobs[job_id] = {"id": job_id, "status": "queued"} #add the job to the jobs dictionary
            self._queue.put((job_id, coordinates)) #add the job to the queue
            if not self._worker_started: #check if the worker thread has been started
                self._worker_started = True #mark the worker thread as started
                Thread(target=self._process_jobs, daemon=True).start() #start the worker thread
        return job_id #return the job ID of the enqueued route request

    def get(self, job_id: str) -> dict[str, Any] | None: #function to retrieve the status of a job by its ID
        with self._lock: #acquire the lock to ensure thread-safe access to the jobs dictionary
            job = self._jobs.get(job_id) #get the job from the jobs dictionary
            return dict(job) if job is not None else None #return a copy of the job if it exists, otherwise return None

    def _process_jobs(self) -> None: #function to process jobs from the queue
        while True: #continuously process jobs from the queue
            job_id, coordinates = self._queue.get() #get the next job from the queue
            with self._lock: #acquire the lock to update the job status
                self._jobs[job_id]["status"] = "processing" #mark the job as processing
            try:
                route = self._route_fetcher(*coordinates) #fetch the route using the route fetcher function
            except (
                HTTPException,
                OSError,
                URLError,
                TimeoutError,
                JSONDecodeError,
                ValueError,
            ) as error: #catch various exceptions that may occur during route fetching
                with self._lock: #acquire the lock to update the job status
                    self._jobs[job_id].update(
                        status="failed",
                        error=f"Route lookup failed: {error}",
                    )
            else: #if no exception occurred, update the job status to completed
                with self._lock: #acquire the lock to update the job status
                    self._jobs[job_id].update(
                        status="completed",
                        route=route,
                    )
            finally: #ensure the job is marked as done in the queue
                self._queue.task_done()


app.config["ROUTE_REQUEST_QUEUE"] = RouteRequestQueue() #initialize the route request queue in the application configuration


def get_db_connection(): #function used to connect to the SQLite database
    db_path = current_app.config["DATABASE"]
    connection = sqlite3.connect(db_path) #create a connection to the SQLite database
    connection.row_factory = sqlite3.Row #enable row factory to access columns by name
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS locations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL
        )
        """
    )
    return connection #return the database connection

@app.route("/") 
def home():
    connection = get_db_connection() #get a connection to the SQLite database
    try:
        locations = connection.execute("SELECT * FROM locations").fetchall()
    finally:
        connection.close()

    return render_template("2ndindex_w_saved_route_coords - Copy.html", locations=locations)

@app.route("/locations")
def get_locations():
    connection = get_db_connection() #get a connection to the SQLite database

    try:
        locations = connection.execute( #execute a SQL query to fetch all locations from the database
            "SELECT * FROM locations"
            ).fetchall() #fetch all locations from the database
        
        return jsonify([dict(location) for location in locations]) #return the locations as a JSON response
    finally:
        connection.close() #close the database connection


@app.route("/api/route-requests", methods=["POST"]) #endpoint to enqueue a new route request
def enqueue_route_request(): #function to handle the enqueueing of a new route request
    if not request.is_json:
        return jsonify(error="Expected a JSON request body."), 400 #return an error if the request body is not JSON

    payload = request.get_json()
    if not isinstance(payload, dict):
        return jsonify(error="Expected a JSON object."), 400 #return an error if the request body is not a JSON object

    start_id = payload.get("start_id") #extract the start location ID from the request payload
    end_id = payload.get("end_id") #extract the end location ID from the request payload
    if type(start_id) is not int or type(end_id) is not int: #check if start_id and end_id are integers
        return jsonify(error="start_id and end_id must be integers."), 400 #return an error if start_id or end_id is not an integer
    if start_id == end_id: #check if start_id and end_id are the same
        return jsonify(error="Choose two different locations."), 400 #return an error if start_id and end_id are the same

    connection = get_db_connection()
    try:
        locations = connection.execute( #execute a SQL query to fetch the start and end locations from the database
            "SELECT id, latitude, longitude FROM locations WHERE id IN (?, ?)",
            (start_id, end_id),
        ).fetchall() #fetch the locations from the database
    finally:
        connection.close()

    locations_by_id = {location["id"]: location for location in locations} #create a dictionary of locations keyed by their ID
    if start_id not in locations_by_id or end_id not in locations_by_id: #check if both start and end locations exist
        return jsonify(error="One or both locations were not found."), 404 #return an error if one or both locations are not found

    start = locations_by_id[start_id] #get the start location from the dictionary
    end = locations_by_id[end_id] #get the end location from the dictionary
    coordinates = ( #create a tuple of coordinates for the route request
        start["longitude"],
        start["latitude"],
        end["longitude"],
        end["latitude"],
    )
    queue_service: RouteRequestQueue = current_app.config["ROUTE_REQUEST_QUEUE"] #get the route request queue service
    job_id = queue_service.enqueue(coordinates) #enqueue the route request with the coordinates
    return jsonify(id=job_id, status="queued"), 202 #return the job ID and status as a JSON response


@app.route("/api/route-requests/<job_id>") #endpoint to get the status of a route request
def get_route_request(job_id: str): #function to handle the retrieval of a route request status
    queue_service: RouteRequestQueue = current_app.config["ROUTE_REQUEST_QUEUE"]
    job = queue_service.get(job_id)
    if job is None:
        return jsonify(error="Route request was not found."), 404 #return an error if the route request is not found
    return jsonify(job) #return the job details as a JSON response


@app.route("/api/saved-routes", methods=["POST"]) #endpoint to save a route
def save_route(): #function to handle the saving of a route
    if not request.is_json:
        return jsonify(error="Expected a JSON request body."), 400 #return an error if the request body is not JSON

    payload = request.get_json() #get the JSON payload from the request body
    if not isinstance(payload, dict): #check if the payload is a dictionary
        return jsonify(error="Expected a JSON object."), 400 #return an error if the request body is not a JSON object

    start_id = payload.get("start_id") #get the start location ID from the payload
    end_id = payload.get("end_id") #get the end location ID from the payload
    route_data = payload.get("route")
    route_candidates = payload.get("route_candidates", [route_data])
    if type(start_id) is not int or type(end_id) is not int: #check if start_id and end_id are integers
        return jsonify(error="start_id and end_id must be integers."), 400 #return an error if start_id or end_id is not an integer
    if start_id == end_id: #check if start_id and end_id are the same
        return jsonify(error="Choose two different locations."), 400 #return an error if start_id and end_id are the same
    if not isinstance(route_data, dict):
        return jsonify(error="A planned route is required to save."), 400
    if (
        not isinstance(route_candidates, list)
        or not route_candidates
        or len(route_candidates) > 5
        or any(not isinstance(candidate, dict) for candidate in route_candidates)
    ):
        return jsonify(error="route_candidates must contain between 1 and 5 route objects."), 400

    for candidate in route_candidates:
        candidate_distance = candidate.get("distance")
        candidate_duration = candidate.get("duration")
        if (
            not isinstance(candidate.get("geometry"), dict)
            or isinstance(candidate_distance, bool)
            or not isinstance(candidate_distance, (int, float))
            or not math.isfinite(candidate_distance)
            or isinstance(candidate_duration, bool)
            or not isinstance(candidate_duration, (int, float))
            or not math.isfinite(candidate_duration)
            or not isinstance(candidate.get("legs"), list)
        ):
            return jsonify(error="A route candidate is incomplete or invalid."), 400

    try:
        route_selection = Request.select_best_route(
            route_candidates,
            database_path=Request.SECTOR_DATABASE_PATH,
        )
    except ValueError as error:
        return jsonify(error=str(error)), 400
    except Request.R2ConfigurationError as error:
        return jsonify(error=f"R2 image downloads are not configured: {error}"), 503
    except Request.R2DownloadError as error:
        return jsonify(error=f"R2 image downloads failed: {error}"), 502
    except Request.RoadClassifierError as error:
        return jsonify(error=f"Road classification failed: {error}"), 500

    route_data = route_selection["route"]
    segments = route_selection["segments"]

    validated_segments = []
    for index, segment in enumerate(segments):
        if not isinstance(segment, dict): #check if each segment is a dictionary
            return jsonify(error=f"Segment {index + 1} must be a JSON object."), 400 #return an error if the segment is not a JSON object

        road_name = segment.get("Roadname")
        start = segment.get("Start LatLon")
        end = segment.get("End LatLon")
        if (
            not isinstance(road_name, str) #check if road_name is a string
            or not road_name.strip() #check if road_name is not empty
            or not isinstance(start, list) #check if start is a list
            or len(start) != 2 #check if start has exactly 2 elements
            or not isinstance(end, list) #check if end is a list
            or len(end) != 2 #check if end has exactly 2 elements
        ):
            return jsonify(error=f"Segment {index + 1} has an invalid shape."), 400 #return an error if the segment has an invalid shape

        coordinates = (*start, *end)
        if any(
            isinstance(value, bool) #check if any coordinate is a boolean
            or not isinstance(value, (int, float)) #check if any coordinate is not a number
            for value in coordinates
        ):
            return jsonify(error=f"Segment {index + 1} has invalid coordinates."), 400 #return an error if the segment has invalid coordinates
        start_latitude, start_longitude, end_latitude, end_longitude = coordinates
        if (
            not -90 <= start_latitude <= 90 #check if start_latitude is within the valid range
            or not -180 <= start_longitude <= 180 #check if start_longitude is within the valid range
            or not -90 <= end_latitude <= 90 #check if end_latitude is within the valid range
            or not -180 <= end_longitude <= 180 #check if end_longitude is within the valid range
        ):
            return jsonify(error=f"Segment {index + 1} coordinates are out of range."), 400 #return an error if the segment coordinates are out of range
        if any(not math.isfinite(value) for value in coordinates): #check if any coordinate is not finite
            return jsonify(error=f"Segment {index + 1} has invalid coordinates."), 400 #return an error if the segment has invalid coordinates

        validated_segments.append( #add the validated segment to the list of validated segments
            (
                road_name.strip(),
                start_latitude,
                start_longitude,
                end_latitude,
                end_longitude,
            )
        )

    stored_segments = [
        {
            "Roadname": road_name,
            "Start LatLon": [start_latitude, start_longitude],
            "End LatLon": [end_latitude, end_longitude],
        }
        for road_name, start_latitude, start_longitude, end_latitude, end_longitude
        in validated_segments
    ]

    connection = get_db_connection() #get a database connection
    try:
        with connection: #use the connection as a context manager
            connection.execute( #execute the SQL command to create the saved_routes table if it doesn't exist
                """
                CREATE TABLE IF NOT EXISTS saved_routes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    start_location_id INTEGER NOT NULL REFERENCES locations(id),
                    end_location_id INTEGER NOT NULL REFERENCES locations(id),
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            connection.execute( #execute the SQL command to create the saved_route_segments table if it doesn't exist
                """
                CREATE TABLE IF NOT EXISTS saved_route_segments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    route_id INTEGER NOT NULL REFERENCES saved_routes(id) ON DELETE CASCADE,
                    segment_order INTEGER NOT NULL,
                    road_name TEXT NOT NULL,
                    start_latitude REAL NOT NULL,
                    start_longitude REAL NOT NULL,
                    end_latitude REAL NOT NULL,
                    end_longitude REAL NOT NULL,
                    UNIQUE (route_id, segment_order)
                )
                """
            )
            locations = connection.execute(
                "SELECT id FROM locations WHERE id IN (?, ?)",
                (start_id, end_id),
            ).fetchall() #fetch all the locations with the given start and end IDs
            if len(locations) != 2: #check if both locations were found
                return jsonify(error="One or both locations were not found."), 404 #return an error if one or both locations were not found

            cursor = connection.execute( #execute the SQL command to insert a new saved route
                """
                INSERT INTO saved_routes (start_location_id, end_location_id)
                VALUES (?, ?)
                """,
                (start_id, end_id),
            )
            route_id = cursor.lastrowid #get the ID of the newly inserted saved route
            connection.executemany( #execute the SQL command to insert the saved route segments
                """
                INSERT INTO saved_route_segments (
                    route_id, segment_order, road_name,
                    start_latitude, start_longitude, end_latitude, end_longitude
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (route_id, order, *segment) #create a tuple for each segment with the route ID, segment order, and segment details
                    for order, segment in enumerate(validated_segments) #enumerate the validated segments to get the order and segment details
                ],
            )
    finally:
        connection.close()

    route_save_result = Request.save_route(
        route_data,
        route_id=route_id,
        start_id=start_id,
        end_id=end_id,
        segments=stored_segments,
        classification_result=route_selection["evaluation"],
    )
    return jsonify(
        id=route_id,
        saved_segments=len(validated_segments),
        sectors=route_save_result["sectors"],
        downloaded_images=route_save_result["downloaded_images"],
        missing_images=route_save_result["missing_images"],
        classification_output=route_save_result["classification_output"],
        cnn_average=route_save_result["cnn_average"],
        route_comparisons=route_save_result["comparisons"],
        selected_route_index=route_save_result["selected_route_index"],
        selected_route=route_data,
    ), 201 #return the ID of the newly created saved route and the number of saved segments


if __name__ == "__main__":
    app.run(host="127.0.0.1", debug=True)