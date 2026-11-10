import json  # Import the utilities used by this module.
import math  # Import the utilities used by this module.
import os  # Import the utilities used by this module.
import re  # Import the utilities used by this module.
import shutil  # Import the utilities used by this module.
import sqlite3  # Import the utilities used by this module.
import subprocess  # Import the utilities used by this module.
import sys  # Import the utilities used by this module.
import tempfile  # Import the utilities used by this module.
from concurrent.futures import ThreadPoolExecutor, as_completed  # Import the utilities used by this module.
from pathlib import Path  # Import the utilities used by this module.
from pathlib import PurePosixPath  # Import the utilities used by this module.
from threading import Lock  # Import the utilities used by this module.
from typing import Any  # Import the utilities used by this module.


ROUTE_STORAGE_PATH = Path(__file__).with_name("Route_storage.json")  # Set ROUTE_STORAGE_PATH for the operation below.
SECTOR_DATABASE_PATH = Path(__file__).with_name("naviGator_camcountyUpdated_db.db")  # Set SECTOR_DATABASE_PATH for the operation below.
R2_BUCKET_NAME = "camden-county-street-images"  # Set R2_BUCKET_NAME for the operation below.
R2_ACCOUNT_ID = "7e641eadc881f6ff1bed3efd05a3fc2f"  # Set R2_ACCOUNT_ID for the operation below.
ROAD_CLASSIFIER_PATH = Path(__file__).with_name("road_classifier.py")  # Set ROAD_CLASSIFIER_PATH for the operation below.
ROAD_CLASSIFIER_PYTHON = Path(  # Set ROAD_CLASSIFIER_PYTHON for the operation below.
    os.environ.get(  # Perform the next step in the current operation.
        "ROAD_CLASSIFIER_PYTHON",  # Continue the current value or expression.
        str(  # Perform the next step in the current operation.
            Path(__file__).with_name(".venv-classifier")  # Perform the next step in the current operation.
            / ("Scripts/python.exe" if os.name == "nt" else "bin/python")  # Perform the next step in the current operation.
        ),  # Continue or close the surrounding expression.
    )  # Continue or close the surrounding expression.
)  # Continue or close the surrounding expression.
_storage_lock = Lock()  # Set _storage_lock for the operation below.

route: dict[str, Any] | None = None  # Perform the next step in the current operation.


class R2ConfigurationError(RuntimeError):  # Define R2ConfigurationError as a module-specific error type.
    pass  # Leave this exception type without extra behavior.


class R2DownloadError(RuntimeError):  # Define R2DownloadError as a module-specific error type.
    pass  # Leave this exception type without extra behavior.


class RoadClassifierError(RuntimeError):  # Define RoadClassifierError as a module-specific error type.
    pass  # Leave this exception type without extra behavior.


def _parse_classifier_results(output: str) -> dict[str, tuple[float, int, str]]:  # Define _parse_classifier_results to parse classifier output into per-road scores.
    predictions: dict[str, tuple[float, int, str]] = {}  # Perform the next step in the current operation.
    pattern = re.compile(  # Set pattern for the operation below.
        r"^(.+): avg (\d+(?:\.\d+)?)/5\s+\(worst \d+, best \d+, (\d+) segments\)$"  # Perform the next step in the current operation.
    )  # Continue or close the surrounding expression.
    for line in output.splitlines():  # Process each item in this collection.
        match = pattern.match(line.strip())  # Set match for the operation below.
        if match:  # Check whether the condition requires this branch.
            road_key, average, segment_count = match.groups()  # Perform the next step in the current operation.
            predictions[road_key] = (float(average), int(segment_count), line.strip())  # Perform the next step in the current operation.
    return predictions  # Return the computed result to the caller.


def _route_classifier_keys(  # Define _route_classifier_keys to find image keys for route roads and sectors.
    segments: list[dict[str, Any]],  # Continue the surrounding argument or collection list.
    sectors: list[str],  # Continue the surrounding argument or collection list.
    database_path: str | Path,  # Continue the surrounding argument or collection list.
) -> set[str]:  # Begin the indented block for this operation.
    road_names = list(dict.fromkeys(  # Set road_names for the operation below.
        segment["Roadname"].strip()  # Perform the next step in the current operation.
        for segment in segments  # Process each item in this collection.
        if isinstance(segment.get("Roadname"), str) and segment["Roadname"].strip()  # Check whether the condition requires this branch.
    ))  # Perform the next step in the current operation.
    if not road_names or not sectors:  # Check whether the condition requires this branch.
        return set()  # Return the computed result to the caller.

    sector_placeholders = ", ".join("?" for _ in sectors)  # Set sector_placeholders for the operation below.
    road_placeholders = ", ".join("?" for _ in road_names)  # Set road_placeholders for the operation below.
    connection = sqlite3.connect(database_path)  # Set connection for the operation below.
    try:  # Begin a block whose errors are handled below.
        rows = connection.execute(  # Set rows for the operation below.
            # Start the database query for image keys matching the route.
            f"""
            SELECT DISTINCT Segments.Photo_file  -- Select unique image object keys.
            FROM Sector  -- Read the matching sector records.
            JOIN Road ON Road.SectorID = Sector.SectorID  -- Match roads to their sectors.
            JOIN Segments ON Segments.RoadID = Road.RoadID  -- Match image records to roads.
            WHERE Sector.Sector_Name IN ({sector_placeholders})  -- Limit results to route sectors.
              AND trim(Road.Road_Name) COLLATE NOCASE IN ({road_placeholders})  -- Match road names without case differences.
              AND Segments.Photo_file IS NOT NULL  -- Exclude records without an image key.
              AND trim(Segments.Photo_file) <> ''  -- Exclude empty image keys.
            """,  # Start or end the SQL query text.
            (*sectors, *road_names),  # Continue the surrounding argument or collection list.
        ).fetchall()  # Perform the next step in the current operation.
    finally:  # Run cleanup regardless of the outcome.
        connection.close()  # Perform the next step in the current operation.

    keys: set[str] = set()  # Perform the next step in the current operation.
    for (photo_file,) in rows:  # Process each item in this collection.
        stem = PurePosixPath(photo_file.replace("\\", "/")).stem  # Set stem for the operation below.
        if "_" in stem:  # Check whether the condition requires this branch.
            keys.add(stem.rsplit("_", 1)[0])  # Perform the next step in the current operation.
    return keys  # Return the computed result to the caller.


def select_best_route(  # Define select_best_route to score route candidates and choose the best one.
    route_candidates: list[dict[str, Any]],  # Continue the surrounding argument or collection list.
    database_path: str | Path = SECTOR_DATABASE_PATH,  # Continue the surrounding argument or collection list.
    *,  # Continue the surrounding argument or collection list.
    r2_client: Any | None = None,  # Continue the surrounding argument or collection list.
) -> dict[str, Any]:  # Begin the indented block for this operation.
    if not route_candidates:  # Check whether the condition requires this branch.
        raise ValueError("At least one route candidate is required.")  # Report the error to the caller.

    candidates: list[dict[str, Any]] = []  # Perform the next step in the current operation.
    all_sectors: list[str] = []  # Perform the next step in the current operation.
    seen_sectors: set[str] = set()  # Perform the next step in the current operation.
    all_segments: list[dict[str, Any]] = []  # Perform the next step in the current operation.
    for index, route_data in enumerate(route_candidates):  # Process each item in this collection.
        segments = extract_route_segments(route_data)  # Set segments for the operation below.
        sectors = find_route_sectors(segments, database_path)  # Set sectors for the operation below.
        classifier_keys = _route_classifier_keys(segments, sectors, database_path)  # Set classifier_keys for the operation below.
        candidates.append(  # Perform the next step in the current operation.
            {  # Continue or close the surrounding expression.
                "index": index,  # Continue the current value or expression.
                "route": route_data,  # Continue the current value or expression.
                "segments": segments,  # Continue the current value or expression.
                "sectors": sectors,  # Continue the current value or expression.
                "classifier_keys": classifier_keys,  # Continue the current value or expression.
            }  # Continue or close the surrounding expression.
        )  # Continue or close the surrounding expression.
        all_segments.extend(segments)  # Perform the next step in the current operation.
        for sector in sectors:  # Process each item in this collection.
            if sector not in seen_sectors:  # Check whether the condition requires this branch.
                seen_sectors.add(sector)  # Perform the next step in the current operation.
                all_sectors.append(sector)  # Perform the next step in the current operation.

    image_directory, downloaded_images, missing_images = download_route_sector_images(  # Perform the next step in the current operation.
        all_sectors,  # Continue the surrounding argument or collection list.
        all_segments,  # Continue the surrounding argument or collection list.
        database_path,  # Continue the surrounding argument or collection list.
        r2_client=r2_client,  # Set r2_client for the operation below.
    )  # Continue or close the surrounding expression.
    predictions: dict[str, tuple[float, int, str]] = {}  # Perform the next step in the current operation.
    try:  # Begin a block whose errors are handled below.
        if image_directory is not None:  # Check whether the condition requires this branch.
            predictions = _parse_classifier_results(run_road_classifier(image_directory))  # Set predictions for the operation below.
    finally:  # Run cleanup regardless of the outcome.
        if image_directory is not None:  # Check whether the condition requires this branch.
            shutil.rmtree(image_directory)  # Perform the next step in the current operation.

    comparisons: list[dict[str, Any]] = []  # Perform the next step in the current operation.
    scores_by_index: dict[int, float | None] = {}  # Perform the next step in the current operation.
    for candidate in candidates:  # Process each item in this collection.
        matched_predictions = [  # Set matched_predictions for the operation below.
            predictions[key]  # Perform the next step in the current operation.
            for key in sorted(candidate["classifier_keys"])  # Process each item in this collection.
            if key in predictions  # Check whether the condition requires this branch.
        ]  # Continue or close the surrounding expression.
        segment_total = sum(count for _, count, _ in matched_predictions)  # Set segment_total for the operation below.
        score = (  # Set score for the operation below.
            sum(average * count for average, count, _ in matched_predictions) / segment_total  # Perform the next step in the current operation.
            if segment_total  # Check whether the condition requires this branch.
            else None  # Perform the next step in the current operation.
        )  # Continue or close the surrounding expression.
        route_data = candidate["route"]  # Set route_data for the operation below.
        scores_by_index[candidate["index"]] = score  # Perform the next step in the current operation.
        comparisons.append(  # Perform the next step in the current operation.
            {  # Continue or close the surrounding expression.
                "index": candidate["index"],  # Continue the current value or expression.
                "cnn_average": round(score, 2) if score is not None else None,  # Continue the current value or expression.
                "cnn_segments": segment_total,  # Continue the current value or expression.
                "distance": route_data["distance"],  # Continue the current value or expression.
                "duration": route_data["duration"],  # Continue the current value or expression.
                "classification_output": "\n".join(  # Continue the current value or expression.
                    line for _, _, line in matched_predictions  # Perform the next step in the current operation.
                ),  # Continue or close the surrounding expression.
                "sectors": candidate["sectors"],  # Continue the current value or expression.
                "downloaded_images": downloaded_images,  # Continue the current value or expression.
                "missing_images": missing_images,  # Continue the current value or expression.
            }  # Continue or close the surrounding expression.
        )  # Continue or close the surrounding expression.

    scored = [item for item in comparisons if item["cnn_average"] is not None]  # Set scored for the operation below.
    selection_pool = scored if scored else comparisons  # Set selection_pool for the operation below.
    best_comparison = min(  # Set best_comparison for the operation below.
        selection_pool,  # Continue the surrounding argument or collection list.
        key=lambda item: (  # Set key for the operation below.
            -(scores_by_index[item["index"]] or 0),  # Continue the surrounding argument or collection list.
            item["duration"],  # Continue the surrounding argument or collection list.
            item["distance"],  # Continue the surrounding argument or collection list.
        ),  # Continue or close the surrounding expression.
    )  # Continue or close the surrounding expression.
    best = candidates[best_comparison["index"]]  # Set best for the operation below.
    best_evaluation = {  # Set best_evaluation for the operation below.
        "sectors": best["sectors"],  # Continue the current value or expression.
        "downloaded_images": downloaded_images,  # Continue the current value or expression.
        "missing_images": missing_images,  # Continue the current value or expression.
        "classification_output": best_comparison["classification_output"],  # Continue the current value or expression.
        "cnn_average": best_comparison["cnn_average"],  # Continue the current value or expression.
        "cnn_segments": best_comparison["cnn_segments"],  # Continue the current value or expression.
        "comparisons": comparisons,  # Continue the current value or expression.
        "selected_route_index": best["index"],  # Continue the current value or expression.
    }  # Continue or close the surrounding expression.
    return {  # Return the computed result to the caller.
        "route": best["route"],  # Continue the current value or expression.
        "segments": best["segments"],  # Continue the current value or expression.
        "evaluation": best_evaluation,  # Continue the current value or expression.
    }  # Continue or close the surrounding expression.


def run_road_classifier(image_directory: Path) -> str:  # Define run_road_classifier to run the classifier and return its output.
    if not ROAD_CLASSIFIER_PYTHON.is_file():  # Check whether the condition requires this branch.
        raise RoadClassifierError(  # Report the error to the caller.
            f"Classifier Python was not found at {ROAD_CLASSIFIER_PYTHON}. "  # Continue the current value or expression.
            "Set ROAD_CLASSIFIER_PYTHON to the Python executable with TensorFlow installed."  # Continue the current value or expression.
        )  # Continue or close the surrounding expression.
    if not ROAD_CLASSIFIER_PATH.is_file():  # Check whether the condition requires this branch.
        raise RoadClassifierError(f"Classifier script was not found at {ROAD_CLASSIFIER_PATH}.")  # Report the error to the caller.

    try:  # Begin a block whose errors are handled below.
        result = subprocess.run(  # Set result for the operation below.
            [  # Continue or close the surrounding expression.
                str(ROAD_CLASSIFIER_PYTHON),  # Continue the surrounding argument or collection list.
                str(ROAD_CLASSIFIER_PATH),  # Continue the surrounding argument or collection list.
                str(image_directory),  # Continue the surrounding argument or collection list.
            ],  # Continue or close the surrounding expression.
            cwd=ROAD_CLASSIFIER_PATH.parent,  # Set cwd for the operation below.
            capture_output=True,  # Set capture_output for the operation below.
            check=False,  # Set check for the operation below.
            text=True,  # Set text for the operation below.
            timeout=600,  # Set timeout for the operation below.
        )  # Continue or close the surrounding expression.
    except (OSError, subprocess.TimeoutExpired) as error:  # Handle the specified error condition.
        raise RoadClassifierError(f"Could not run the road classifier: {error}") from error  # Report the error to the caller.

    if result.returncode != 0:  # Check whether the condition requires this branch.
        detail = result.stderr.strip() or result.stdout.strip() or "No diagnostic output was produced."  # Set detail for the operation below.
        raise RoadClassifierError(f"The road classifier failed: {detail}")  # Report the error to the caller.
    return result.stdout.strip()  # Return the computed result to the caller.


def _create_r2_client() -> Any:  # Define _create_r2_client to configure a Cloudflare R2 client.
    account_id = os.environ.get("CLOUDFLARE_ACCOUNT_ID", R2_ACCOUNT_ID)  # Set account_id for the operation below.
    access_key_id = os.environ.get("CLOUDFLARE_R2_ACCESS_KEY_ID")  # Set access_key_id for the operation below.
    secret_access_key = os.environ.get("CLOUDFLARE_R2_SECRET_ACCESS_KEY")  # Set secret_access_key for the operation below.
    missing_settings = [  # Set missing_settings for the operation below.
        name  # Perform the next step in the current operation.
        for name, value in (  # Process each item in this collection.
            ("CLOUDFLARE_R2_ACCESS_KEY_ID", access_key_id),  # Continue the surrounding argument or collection list.
            ("CLOUDFLARE_R2_SECRET_ACCESS_KEY", secret_access_key),  # Continue the surrounding argument or collection list.
        )  # Continue or close the surrounding expression.
        if not value  # Check whether the condition requires this branch.
    ]  # Continue or close the surrounding expression.
    if missing_settings:  # Check whether the condition requires this branch.
        raise R2ConfigurationError(  # Report the error to the caller.
            "Set the R2 environment variables before downloading images: "  # Continue the current value or expression.
            + ", ".join(missing_settings)  # Perform the next step in the current operation.
        )  # Continue or close the surrounding expression.

    try:  # Begin a block whose errors are handled below.
        import boto3  # Import the utilities used by this module.
    except ImportError as error:  # Handle the specified error condition.
        raise R2ConfigurationError(  # Report the error to the caller.
            "R2 image downloads require boto3. Install it with "  # Continue the current value or expression.
            "`python -m pip install -r requirements-r2.txt`."  # Continue the current value or expression.
        ) from error  # Perform the next step in the current operation.

    return boto3.client(  # Return the computed result to the caller.
        "s3",  # Continue the current value or expression.
        endpoint_url=f"https://{account_id}.r2.cloudflarestorage.com",  # Set endpoint_url for the operation below.
        aws_access_key_id=access_key_id,  # Set aws_access_key_id for the operation below.
        aws_secret_access_key=secret_access_key,  # Set aws_secret_access_key for the operation below.
        region_name="auto",  # Set region_name for the operation below.
    )  # Continue or close the surrounding expression.


def _download_object(client: Any, object_key: str, destination: Path) -> bool:  # Define _download_object to download one R2 object to disk.
    try:  # Begin a block whose errors are handled below.
        from botocore.exceptions import BotoCoreError, ClientError  # Import the utilities used by this module.
    except ImportError as error:  # Handle the specified error condition.
        raise R2ConfigurationError(  # Report the error to the caller.
            "R2 image downloads require boto3. Install it with "  # Continue the current value or expression.
            "`python -m pip install -r requirements-r2.txt`."  # Continue the current value or expression.
        ) from error  # Perform the next step in the current operation.

    try:  # Begin a block whose errors are handled below.
        response = client.get_object(Bucket=R2_BUCKET_NAME, Key=object_key)  # Set response for the operation below.
        body = response["Body"]  # Set body for the operation below.
        try:  # Begin a block whose errors are handled below.
            with destination.open("wb") as image_file:  # Manage this resource for the block below.
                while True:  # Repeat while this condition remains true.
                    chunk = body.read(1024 * 1024)  # Set chunk for the operation below.
                    if not chunk:  # Check whether the condition requires this branch.
                        break  # Stop the current loop.
                    image_file.write(chunk)  # Perform the next step in the current operation.
        finally:  # Run cleanup regardless of the outcome.
            body.close()  # Perform the next step in the current operation.
    except ClientError as error:  # Handle the specified error condition.
        error_code = error.response.get("Error", {}).get("Code")  # Set error_code for the operation below.
        if error_code in {"NoSuchKey", "NotFound", "404"}:  # Check whether the condition requires this branch.
            return False  # Return the computed result to the caller.
        raise R2DownloadError(  # Report the error to the caller.
            f"Could not download R2 object {object_key}: {error}"  # Continue the current value or expression.
        ) from error  # Perform the next step in the current operation.
    except BotoCoreError as error:  # Handle the specified error condition.
        raise R2DownloadError(  # Report the error to the caller.
            f"Could not download R2 object {object_key}: {error}"  # Continue the current value or expression.
        ) from error  # Perform the next step in the current operation.
    return True  # Return the computed result to the caller.


def download_route_sector_images(  # Define download_route_sector_images to download images matching route roads.
    sectors: list[str],  # Continue the surrounding argument or collection list.
    segments: list[dict[str, Any]],  # Continue the surrounding argument or collection list.
    database_path: str | Path = SECTOR_DATABASE_PATH,  # Continue the surrounding argument or collection list.
    *,  # Continue the surrounding argument or collection list.
    r2_client: Any | None = None,  # Continue the surrounding argument or collection list.
) -> tuple[Path | None, int, list[str]]:  # Begin the indented block for this operation.
    road_names: list[str] = []  # Perform the next step in the current operation.
    seen_road_names: set[str] = set()  # Perform the next step in the current operation.
    for segment in segments:  # Process each item in this collection.
        road_name = segment.get("Roadname")  # Set road_name for the operation below.
        if not isinstance(road_name, str) or not road_name.strip():  # Check whether the condition requires this branch.
            continue  # Skip to the next loop item.
        normalized_name = road_name.strip().casefold()  # Set normalized_name for the operation below.
        if normalized_name not in seen_road_names:  # Check whether the condition requires this branch.
            seen_road_names.add(normalized_name)  # Perform the next step in the current operation.
            road_names.append(road_name.strip())  # Perform the next step in the current operation.

    if not sectors or not road_names:  # Check whether the condition requires this branch.
        return None, 0, []  # Return the computed result to the caller.

    sector_placeholders = ", ".join("?" for _ in sectors)  # Set sector_placeholders for the operation below.
    road_placeholders = ", ".join("?" for _ in road_names)  # Set road_placeholders for the operation below.
    connection = sqlite3.connect(database_path)  # Set connection for the operation below.
    try:  # Begin a block whose errors are handled below.
        rows = connection.execute(  # Set rows for the operation below.
            # Start the database query for images matching route roads.
            f"""
            SELECT DISTINCT Sector.Sector_Name, Segments.Photo_file  -- Select unique sector-image pairs.
            FROM Sector  -- Read the matching sector records.
            JOIN Road ON Road.SectorID = Sector.SectorID  -- Match roads to their sectors.
            JOIN Segments ON Segments.RoadID = Road.RoadID  -- Match image records to roads.
            WHERE Sector.Sector_Name IN ({sector_placeholders})  -- Limit results to route sectors.
              AND trim(Road.Road_Name) COLLATE NOCASE IN ({road_placeholders})  -- Match road names without case differences.
              AND Segments.Photo_file IS NOT NULL  -- Exclude records without an image key.
              AND trim(Segments.Photo_file) <> ''  -- Exclude empty image keys.
            ORDER BY Sector.Sector_Name, Segments.Photo_file  -- Sort the image list consistently.
            """,  # Start or end the SQL query text.
            (*sectors, *road_names),  # Continue the surrounding argument or collection list.
        ).fetchall()  # Perform the next step in the current operation.
    finally:  # Run cleanup regardless of the outcome.
        connection.close()  # Perform the next step in the current operation.

    if not rows:  # Check whether the condition requires this branch.
        return None, 0, []  # Return the computed result to the caller.

    client = r2_client if r2_client is not None else _create_r2_client()  # Set client for the operation below.
    download_directory = Path(tempfile.mkdtemp(prefix="route-sector-images-"))  # Set download_directory for the operation below.
    completed = False  # Set completed for the operation below.
    try:  # Begin a block whose errors are handled below.
        objects_to_download: dict[str, Path] = {}  # Perform the next step in the current operation.
        for _, photo_file in rows:  # Process each item in this collection.
            object_key = photo_file.strip().replace("\\", "/")  # Set object_key for the operation below.
            bucket_prefix = f"{R2_BUCKET_NAME}/"  # Set bucket_prefix for the operation below.
            if object_key.startswith(bucket_prefix):  # Check whether the condition requires this branch.
                object_key = object_key[len(bucket_prefix):]  # Set object_key for the operation below.

            key_path = PurePosixPath(object_key)  # Set key_path for the operation below.
            if not object_key or key_path.is_absolute() or ".." in key_path.parts:  # Check whether the condition requires this branch.
                raise ValueError(f"Unsafe image object path in the database: {photo_file}")  # Report the error to the caller.
            if object_key in objects_to_download:  # Check whether the condition requires this branch.
                continue  # Skip to the next loop item.

            destination = download_directory.joinpath(*key_path.parts)  # Set destination for the operation below.
            destination.parent.mkdir(parents=True, exist_ok=True)  # Perform the next step in the current operation.
            objects_to_download[object_key] = destination  # Perform the next step in the current operation.

        downloaded_keys: set[str] = set()  # Perform the next step in the current operation.
        missing_keys: set[str] = set()  # Perform the next step in the current operation.
        max_workers = min(10, len(objects_to_download))  # Set max_workers for the operation below.
        with ThreadPoolExecutor(max_workers=max_workers) as executor:  # Manage this resource for the block below.
            futures = {  # Set futures for the operation below.
                executor.submit(_download_object, client, object_key, destination): object_key  # Perform the next step in the current operation.
                for object_key, destination in objects_to_download.items()  # Process each item in this collection.
            }  # Continue or close the surrounding expression.
            for future in as_completed(futures):  # Process each item in this collection.
                object_key = futures[future]  # Set object_key for the operation below.
                if future.result():  # Check whether the condition requires this branch.
                    downloaded_keys.add(object_key)  # Perform the next step in the current operation.
                else:  # Handle the remaining case.
                    missing_keys.add(object_key)  # Perform the next step in the current operation.

        completed = True  # Set completed for the operation below.
        if not downloaded_keys:  # Check whether the condition requires this branch.
            shutil.rmtree(download_directory)  # Perform the next step in the current operation.
            return None, 0, sorted(missing_keys)  # Return the computed result to the caller.
        return (  # Return the computed result to the caller.
            download_directory,  # Continue the surrounding argument or collection list.
            len(downloaded_keys),  # Continue the surrounding argument or collection list.
            sorted(missing_keys),  # Continue the surrounding argument or collection list.
        )  # Continue or close the surrounding expression.
    finally:  # Run cleanup regardless of the outcome.
        if not completed:  # Check whether the condition requires this branch.
            shutil.rmtree(download_directory)  # Perform the next step in the current operation.


def _write_route_record(record: dict[str, Any], index: int | None = None) -> int:  # Define _write_route_record to persist a route record safely.
    with _storage_lock:  # Manage this resource for the block below.
        if ROUTE_STORAGE_PATH.exists():  # Check whether the condition requires this branch.
            with ROUTE_STORAGE_PATH.open(encoding="utf-8") as storage_file:  # Manage this resource for the block below.
                storage = json.load(storage_file)  # Set storage for the operation below.
            if not isinstance(storage, dict):  # Check whether the condition requires this branch.
                raise ValueError("Route storage must contain a JSON object.")  # Report the error to the caller.
            routes = storage.setdefault("routes", [])  # Set routes for the operation below.
            if not isinstance(routes, list):  # Check whether the condition requires this branch.
                raise ValueError("The routes entry in route storage must be a JSON array.")  # Report the error to the caller.
        else:  # Handle the remaining case.
            storage = {"routes": []}  # Set storage for the operation below.
            routes = storage["routes"]  # Set routes for the operation below.

        if index is None:  # Check whether the condition requires this branch.
            routes.append(record)  # Perform the next step in the current operation.
            index = len(routes) - 1  # Set index for the operation below.
        else:  # Handle the remaining case.
            if index < 0 or index >= len(routes):  # Check whether the condition requires this branch.
                raise ValueError("The route record is no longer available in route storage.")  # Report the error to the caller.
            routes[index] = record  # Perform the next step in the current operation.

        temporary_path: str | None = None  # Perform the next step in the current operation.
        try:  # Begin a block whose errors are handled below.
            with tempfile.NamedTemporaryFile(  # Manage this resource for the block below.
                mode="w",  # Set mode for the operation below.
                encoding="utf-8",  # Set encoding for the operation below.
                dir=ROUTE_STORAGE_PATH.parent,  # Set dir for the operation below.
                delete=False,  # Set delete for the operation below.
            ) as storage_file:  # Begin the indented block for this operation.
                temporary_path = storage_file.name  # Set temporary_path for the operation below.
                json.dump(storage, storage_file, indent=2)  # Perform the next step in the current operation.
                storage_file.write("\n")  # Perform the next step in the current operation.
                storage_file.flush()  # Perform the next step in the current operation.
                os.fsync(storage_file.fileno())  # Perform the next step in the current operation.
            os.replace(temporary_path, ROUTE_STORAGE_PATH)  # Perform the next step in the current operation.
        finally:  # Run cleanup regardless of the outcome.
            if temporary_path is not None and os.path.exists(temporary_path):  # Check whether the condition requires this branch.
                os.unlink(temporary_path)  # Perform the next step in the current operation.
    return index  # Return the computed result to the caller.


def extract_route_segments(route_data: dict[str, Any]) -> list[dict[str, Any]]:  # Define extract_route_segments to validate and extract road segments.
    legs = route_data.get("legs")  # Set legs for the operation below.
    if not isinstance(legs, list) or not legs:  # Check whether the condition requires this branch.
        raise ValueError("The route response did not include road segments.")  # Report the error to the caller.

    segments: list[dict[str, Any]] = []  # Perform the next step in the current operation.
    for leg in legs:  # Process each item in this collection.
        if not isinstance(leg, dict) or not isinstance(leg.get("steps"), list):  # Check whether the condition requires this branch.
            raise ValueError("The route response did not include road steps.")  # Report the error to the caller.

        for step in leg["steps"]:  # Process each item in this collection.
            if not isinstance(step, dict):  # Check whether the condition requires this branch.
                raise ValueError("A route step was invalid.")  # Report the error to the caller.
            geometry = step.get("geometry")  # Set geometry for the operation below.
            coordinates = geometry.get("coordinates") if isinstance(geometry, dict) else None  # Set coordinates for the operation below.
            if not isinstance(coordinates, list) or not coordinates:  # Check whether the condition requires this branch.
                raise ValueError("A route step did not include coordinates.")  # Report the error to the caller.
            if len(coordinates) == 1:  # Check whether the condition requires this branch.
                continue  # Skip to the next loop item.

            start, end = coordinates[0], coordinates[-1]  # Perform the next step in the current operation.
            if (  # Check whether the condition requires this branch.
                not isinstance(start, list)  # Perform the next step in the current operation.
                or len(start) < 2  # allow an alternative condition.
                or not isinstance(end, list)  # allow an alternative condition.
                or len(end) < 2  # allow an alternative condition.
                or any(  # allow an alternative condition.
                    isinstance(value, bool) or not isinstance(value, (int, float))  # Perform the next step in the current operation.
                    for value in (*start[:2], *end[:2])  # Process each item in this collection.
                )  # Continue or close the surrounding expression.
                or any(not math.isfinite(value) for value in (*start[:2], *end[:2]))  # allow an alternative condition.
            ):  # Begin the indented block for this operation.
                raise ValueError("A route step included invalid coordinates.")  # Report the error to the caller.
            if len(coordinates) == 2 and start[:2] == end[:2]:  # Check whether the condition requires this branch.
                continue  # Skip to the next loop item.

            road_name = step.get("name")  # Set road_name for the operation below.
            segments.append(  # Perform the next step in the current operation.
                {  # Continue or close the surrounding expression.
                    "Roadname": road_name.strip() if isinstance(road_name, str) and road_name.strip()  # Continue the current value or expression.
                    else "Unnamed road",  # Continue the surrounding argument or collection list.
                    "Start LatLon": [start[1], start[0]],  # Continue the current value or expression.
                    "End LatLon": [end[1], end[0]],  # Continue the current value or expression.
                }  # Continue or close the surrounding expression.
            )  # Continue or close the surrounding expression.

    if not segments:  # Check whether the condition requires this branch.
        raise ValueError("The route response did not contain any road segments.")  # Report the error to the caller.
    return segments  # Return the computed result to the caller.


def find_route_sectors(  # Define find_route_sectors to find database sectors matching route roads.
    segments: list[dict[str, Any]],  # Continue the surrounding argument or collection list.
    database_path: str | Path = SECTOR_DATABASE_PATH,  # Continue the surrounding argument or collection list.
) -> list[str]:  # Begin the indented block for this operation.
    road_names: list[str] = []  # Perform the next step in the current operation.
    seen_road_names: set[str] = set()  # Perform the next step in the current operation.
    for segment in segments:  # Process each item in this collection.
        road_name = segment.get("Roadname")  # Set road_name for the operation below.
        if not isinstance(road_name, str) or not road_name.strip():  # Check whether the condition requires this branch.
            continue  # Skip to the next loop item.
        normalized_name = road_name.strip().casefold()  # Set normalized_name for the operation below.
        if normalized_name not in seen_road_names:  # Check whether the condition requires this branch.
            seen_road_names.add(normalized_name)  # Perform the next step in the current operation.
            road_names.append(road_name.strip())  # Perform the next step in the current operation.

    if not road_names:  # Check whether the condition requires this branch.
        return []  # Return the computed result to the caller.

    connection = sqlite3.connect(database_path)  # Set connection for the operation below.
    try:  # Begin a block whose errors are handled below.
        sectors: list[str] = []  # Perform the next step in the current operation.
        seen_sectors: set[str] = set()  # Perform the next step in the current operation.
        for road_name in road_names:  # Process each item in this collection.
            rows = connection.execute(  # Set rows for the operation below.
                # Start the database query for sectors matching route roads.
                """
                SELECT DISTINCT Sector.Sector_Name -- select matching database values
                FROM Road -- read from the listed database tables
                JOIN Sector ON Sector.SectorID = Road.SectorID -- connect related database records
                WHERE trim(Road.Road_Name) = trim(?) COLLATE NOCASE -- filter database rows
                  AND Sector.Sector_Name IS NOT NULL -- apply an additional filter
                ORDER BY Sector.Sector_Name -- sort the matching rows
                """,  # Close the SQL query string.
                (road_name,),  # Continue the surrounding argument or collection list.
            ).fetchall()  # Perform the next step in the current operation.
            for (sector_name,) in rows:  # Process each item in this collection.
                if sector_name not in seen_sectors:  # Check whether the condition requires this branch.
                    seen_sectors.add(sector_name)  # Perform the next step in the current operation.
                    sectors.append(sector_name)  # Perform the next step in the current operation.
        return sectors  # Return the computed result to the caller.
    finally:  # Run cleanup regardless of the outcome.
        connection.close()  # Perform the next step in the current operation.


def save_route(  # Define save_route to classify and persist a route.
    route_data: dict[str, Any],  # Continue the surrounding argument or collection list.
    *,  # Continue the surrounding argument or collection list.
    route_id: int,  # Continue the surrounding argument or collection list.
    start_id: int,  # Continue the surrounding argument or collection list.
    end_id: int,  # Continue the surrounding argument or collection list.
    segments: list[dict[str, Any]],  # Continue the surrounding argument or collection list.
    database_path: str | Path = SECTOR_DATABASE_PATH,  # Continue the surrounding argument or collection list.
    r2_client: Any | None = None,  # Continue the surrounding argument or collection list.
    classification_result: dict[str, Any] | None = None,  # Continue the surrounding argument or collection list.
) -> dict[str, Any]:  # Begin the indented block for this operation.
    global route  # Declare that this function updates the module-level value.

    if classification_result is None:  # Check whether the condition requires this branch.
        sectors = find_route_sectors(segments, database_path)  # Set sectors for the operation below.
        image_directory, downloaded_images, missing_images = download_route_sector_images(  # Perform the next step in the current operation.
            sectors,  # Continue the surrounding argument or collection list.
            segments,  # Continue the surrounding argument or collection list.
            database_path,  # Continue the surrounding argument or collection list.
            r2_client=r2_client,  # Set r2_client for the operation below.
        )  # Continue or close the surrounding expression.
        classification_output = ""  # Set classification_output for the operation below.
        try:  # Begin a block whose errors are handled below.
            if image_directory is not None:  # Check whether the condition requires this branch.
                classification_output = run_road_classifier(image_directory)  # Set classification_output for the operation below.
        finally:  # Run cleanup regardless of the outcome.
            if image_directory is not None:  # Check whether the condition requires this branch.
                shutil.rmtree(image_directory)  # Perform the next step in the current operation.
        classification_result = {  # Set classification_result for the operation below.
            "sectors": sectors,  # Continue the current value or expression.
            "downloaded_images": downloaded_images,  # Continue the current value or expression.
            "missing_images": missing_images,  # Continue the current value or expression.
            "classification_output": classification_output,  # Continue the current value or expression.
        }  # Continue or close the surrounding expression.

    sectors = classification_result["sectors"]  # Set sectors for the operation below.
    record = {  # Set record for the operation below.
        "id": route_id,  # Continue the current value or expression.
        "start_id": start_id,  # Continue the current value or expression.
        "end_id": end_id,  # Continue the current value or expression.
        "route": route_data,  # Continue the current value or expression.
        "segments": segments,  # Continue the current value or expression.
        "sectors": sectors,  # Continue the current value or expression.
        "downloaded_images": classification_result["downloaded_images"],  # Continue the current value or expression.
        "missing_images": classification_result["missing_images"],  # Continue the current value or expression.
        "classification_output": classification_result["classification_output"],  # Continue the current value or expression.
        "cnn_average": classification_result.get("cnn_average"),  # Continue the current value or expression.
        "cnn_segments": classification_result.get("cnn_segments", 0),  # Continue the current value or expression.
        "route_comparisons": classification_result.get("comparisons", []),  # Continue the current value or expression.
        "selected_route_index": classification_result.get("selected_route_index", 0),  # Continue the current value or expression.
    }  # Continue or close the surrounding expression.
    storage_index = _write_route_record(record)  # Set storage_index for the operation below.
    route = route_data  # Set route for the operation below.
    print("Route saved:")  # Print the diagnostic information.
    print(json.dumps(record, indent=2))  # Print the diagnostic information.
    return {  # Return the computed result to the caller.
        "sectors": sectors,  # Continue the current value or expression.
        "downloaded_images": record["downloaded_images"],  # Continue the current value or expression.
        "missing_images": record["missing_images"],  # Continue the current value or expression.
        "classification_output": record["classification_output"],  # Continue the current value or expression.
        "cnn_average": record["cnn_average"],  # Continue the current value or expression.
        "comparisons": record["route_comparisons"],  # Continue the current value or expression.
        "selected_route_index": record["selected_route_index"],  # Continue the current value or expression.
    }  # Continue or close the surrounding expression.
