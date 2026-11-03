from flask import Flask, current_app, jsonify, render_template, request
from http.client import HTTPException
from json import JSONDecodeError
from queue import Queue
from threading import Lock, Thread
from typing import Any, Callable
from urllib.error import URLError
from urllib.request import urlopen
from uuid import uuid4
import json
import sqlite3
from pathlib import Path

app = Flask(__name__) #using flask to create a web application for routing and navigation


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
    db_path = Path(__file__).with_name("test_navigation.db") #define the path to the SQLite database file
    connection = sqlite3.connect(db_path) #create a connection to the SQLite database
    connection.row_factory = sqlite3.Row #enable row factory to access columns by name
    return connection #return the database connection

@app.route("/") 
def home():
    connection = get_db_connection() #get a connection to the SQLite database
    locations = connection.execute("SELECT * FROM locations").fetchall() #fetch all locations from the database
    connection.close() #close the database connection

    return render_template("routing_index.html", locations=locations) #render the index page with the list of locations

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


if __name__ == "__main__":
    app.run(host="127.0.0.1", debug=True)