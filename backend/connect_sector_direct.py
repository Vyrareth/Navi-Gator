# =====================================================================================
# connect_sector_direct.py
# Connects Don's sectorCoordinateProcessor.py to Cris's SimpleAutoclicker directly.
# Don's functions return the road boxes in memory and they go straight into capture().
#
# HOW TO RUN (works with any sector .tif / .tiff, in any folder)
#
# OUTPUT
#   One folder per sector, one picture per box, named after its road and interval:
#   <Sector>/<Sector>_<Road_Name>_000.png   
#
# BEFORE RUNNING
#   - Put this file in the same folder as sectorCoordinateProcessor.py and SimpleAutoclickerV1.py. and the tiff
#   - The testing section in sectorCoordinateProcessor.py must be inside ''' ''' or it runs on import.
#   - Windows display scaling must be 100%. Needs internet (roads come from OpenStreetMap).
#   - Don't touch the mouse while it runs. Press Esc to stop.
# =====================================================================================

import os
import sys
import glob
import time
import importlib.util

import rasterio

# Don's three functions (see sectorCoordinateProcessor.py):
#   roadsFromSector             -> which roads are in the image
#   sampleIntervals             -> points every 50 ft along one road
#   sampleScreenshotCoordinates -> turns those points into pixel boxes (UL and LR corners)
from sectorCoordinateProcessor import roadsFromSector, sampleIntervals, sampleScreenshotCoordinates

# Load the autoclicker file by its path and call it "autoclicker" in this script.
# (Loading by path keeps working even if the file gets renamed with a version number
#  like "V1.1", which a normal import can't handle.)
_here = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("autoclicker", os.path.join(_here, "SimpleAutoclicker.py"))
autoclicker = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(autoclicker)

# Distance in feet between boxes along a road. At 1 ft per pixel this is also
# the box size in pixels (50 x 50). Change it if the CNN needs bigger pictures.
SAMPLE_DISTANCE = 50


# -------------------------------------------------------------------------------------
# Helper: get the sector name from any file name or path
# -------------------------------------------------------------------------------------
def sector_from_path(tiffPath):
    # "C:\maps\CC_9C.tif" -> "CC_9C",  "CC_14H.tiff" -> "CC_14H"
    return os.path.splitext(os.path.basename(tiffPath))[0]


# -------------------------------------------------------------------------------------
# STEP 1 (Don's part): find all the road boxes in one sector image
# -------------------------------------------------------------------------------------
def find_boxes(tiffPath, sectorName):
    """Returns a list of boxes. Each box is a dictionary like:
    {'SectorName': 'CC_14H', 'RoadName': 'Chews Landing Road', 'intervalNum': 0,
     'ULCoords': (4932, 4506), 'LRCoords': (4982, 4556)}
    ULCoords = upper-left corner, LRCoords = lower-right corner, both as (column, row) pixels."""

    # Image size in pixels (boxes that fall outside the image get thrown out)
    with rasterio.open(tiffPath) as ds:
        width, height = ds.width, ds.height

    # Ask OpenStreetMap which roads are inside this image.
    # roadsDF   = table of roads (name, shape, length), longest road first
    # transform = how to convert map coordinates (feet) into pixel coordinates
    print("Downloading roads from OpenStreetMap (can take a minute)...")
    roadsDF, transform = roadsFromSector(tiffPath)
    print(f"Found {len(roadsDF)} named roads")

    # For every road: get a point every 50 ft, then turn each point into a box
    boxes = []
    for i in range(len(roadsDF)):
        points = sampleIntervals(roadsDF.loc[i, "geometry"], SAMPLE_DISTANCE)
        boxes += sampleScreenshotCoordinates(points, SAMPLE_DISTANCE, transform, sectorName,
                                             roadsDF.loc[i, "name"], width, height)
    print(f"Found {len(boxes)} boxes")
    return boxes


# -------------------------------------------------------------------------------------
# STEP 2 (Cris's part): screenshot every box with the autoclicker
# -------------------------------------------------------------------------------------
def screenshot_boxes(tiffPath, boxes):
    """Screenshots every box and saves it as <Sector>/<Sector>_<Road>_<interval>.png"""

    # Load the big image once here instead of once per box (much faster)
    img = autoclicker.load_image(tiffPath)

    for n, box in enumerate(boxes, 1):
        # Corners as plain Python ints (Don's code can return numpy ints)
        ul = tuple(int(v) for v in box["ULCoords"])
        lr = tuple(int(v) for v in box["LRCoords"])
        print(f"[{n}/{len(boxes)}] {box['RoadName']} #{box['intervalNum']}")

        # Open full screen -> zoom in -> screenshot -> save. Returns the saved file path.
        path = autoclicker.capture(ul, lr, tiffPath, img)

        # If Esc was pressed during that box, stop the whole run
        if autoclicker.stopped["esc"]:
            print("Stopped with Esc")
            break

        # The autoclicker saves pictures as <file name>/<file name>_001.png.
        # Move + rename it so the name says which sector, road and 50 ft stretch it is.
        outDir = box["SectorName"]
        os.makedirs(outDir, exist_ok=True)
        road = box["RoadName"].replace(" ", "_").replace("/", "-")  # no spaces or slashes in file names
        newPath = os.path.join(outDir, f"{box['SectorName']}_{road}_{box['intervalNum']:03d}.png")
        os.replace(path, newPath)
        print("  ->", newPath)

        # If --sector was used, the autoclicker's own folder is now empty: remove it
        try:
            os.rmdir(os.path.dirname(path))
        except OSError:
            pass  # folder not empty or same as outDir - leave it


# -------------------------------------------------------------------------------------
# Run one sector file from start to finish
# -------------------------------------------------------------------------------------
def run_sector(tiffPath, sectorName=None, limit=None):
    sectorName = sectorName or sector_from_path(tiffPath)
    print(f"\n=== {sectorName}  ({tiffPath}) ===")

    # Step 1: find all boxes in the sector
    boxes = find_boxes(tiffPath, sectorName)

    # Optional: only do the first N boxes (for quick tests)
    if limit:
        boxes = boxes[:limit]

    # Short pause so you can take your hand off the mouse
    print("Starting screenshots in 3 seconds - don't touch the mouse. Esc stops.")
    time.sleep(3)

    # Step 2: screenshot every box
    screenshot_boxes(tiffPath, boxes)


# -------------------------------------------------------------------------------------
# MAIN: reads what you typed after  python connect_sector_direct.py
# -------------------------------------------------------------------------------------
if __name__ == "__main__":
    args = sys.argv[1:]

    # --sector NAME  (optional) labels the pictures with NAME instead of the file name
    sectorName = None
    if "--sector" in args:
        i = args.index("--sector")
        sectorName = args[i + 1]
        del args[i:i + 2]

    # A number (optional) = only do the first N boxes
    limit = None
    if args and args[-1].isdigit():
        limit = int(args.pop())

    # No file typed: open a window to pick one
    if not args:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        picked = filedialog.askopenfilename(title="Pick a sector image",
                                            filetypes=[("GeoTIFF", "*.tif *.tiff")])
        root.destroy()
        if not picked:
            sys.exit("No file picked.")
        args = [picked]

    # Turn what was typed into a list of .tif files (a folder means every .tif inside it)
    files = []
    for a in args:
        if os.path.isdir(a):
            files += sorted(glob.glob(os.path.join(a, "*.tif")) + glob.glob(os.path.join(a, "*.tiff")))
        elif os.path.isfile(a):
            files.append(a)
        else:
            print(f"Can't find {a} - check the spelling and folder")

    if not files:
        sys.exit("No .tif files to run.")
    if sectorName and len(files) > 1:
        sys.exit("--sector only works with one file at a time.")

    # Run every file, one after another. Esc stops all of them.
    for f in files:
        run_sector(f, sectorName, limit)
        if autoclicker.stopped["esc"]:
            break
    print("Done.")
