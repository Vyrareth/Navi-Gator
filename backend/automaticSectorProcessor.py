###Navi-Gator Script to retrieve files.
import io
import os
import time
import shutil
import sqlite3
import tempfile
import boto3
import pandas as pd
import geopandas as gpd
import osmnx as ox
from osmnx._errors import InsufficientResponseError
from botocore.config import Config
from rasterio.io import MemoryFile

###import code from Cris
import connect_sector_direct
from connect_sector_direct import (autoclicker, sampleIntervals, sampleScreenshotCoordinates, sector_from_path, safe_road_name)
from sectorCoordinateProcessor import roadsFromSector

###For API Access regarding Cloudflare pulling/uploads.
R2AcctID= ### Change this to yours.
accessIDKey= ### Change this to yours
accessIDSecret=### Change this to yours
jurisSpecEndPoint= ###Change this to yours

###Run settings
MAX_SECTORS=1            ### How many sectors to run (for testing). Set to None to run the whole CSV.
SKIP_FINISHED=True       ### Skip sectors already listed in finishedSectors.txt (lets you resume after Esc / a crash).
FINISHED_LOG='finishedSectors.txt'
FAILED_LOG='failedSectors.csv'

### Overpass (OSM) servers to try, in order. If one times out, the next one is tried.
OVERPASS_MIRRORS=["https://overpass.private.coffee/api", "https://overpass-api.de/api", "https://overpass.kumi.systems/api"]
OSM_ATTEMPTS_PER_MIRROR=2

def fetchRoads(tiffPath, transform):
    ### Calls Don's roadsFromSector, retrying on timeouts / server errors and switching mirrors.
    ### A sector with no roads at all (river, woods) returns an empty table instead of crashing.
    lastError=None
    for mirror in OVERPASS_MIRRORS:
        ox.settings.overpass_url=mirror
        for attempt in range(1, OSM_ATTEMPTS_PER_MIRROR+1):
            try:
                return roadsFromSector(tiffPath)
            except InsufficientResponseError:
                print('No roads found in OSM for this sector.')
                return gpd.GeoDataFrame({'name': [], 'geometry': []}, geometry='geometry'), transform
            except Exception as e:
                lastError=e
                print(f'  OSM request failed ({mirror}, try {attempt}): {e}')
                time.sleep(10*attempt)
    raise RuntimeError(f'All OSM mirrors failed: {lastError}')

def deleteSector(sectorName):
    ### Removes every row for this sector (any SectorID, including old "SEC-<number>" ones) so a re-run never
    ### leaves stale roads/segments or a duplicate sector behind.
    oldIDs=[r[0] for r in cursor.execute("SELECT SectorID FROM Sector WHERE Sector_Name=?;", (sectorName,))]
    for sid in oldIDs:
        cursor.execute("DELETE FROM Segments WHERE RoadID IN (SELECT RoadID FROM Road WHERE SectorID=?);", (sid,))
        cursor.execute("DELETE FROM Road WHERE SectorID=?;", (sid,))
        cursor.execute("DELETE FROM Sector WHERE SectorID=?;", (sid,))

### Set up database
dbName="naviGator_camcountyUpdated_db.db"
conn=sqlite3.connect(dbName)
cursor=conn.cursor()

# Enforce foreign key structures
cursor.execute("PRAGMA foreign_keys = ON;")

# Ensure the parent County (Camden) and State (NJ) records exist to satisfy Foreign Key constraints
cursor.execute("INSERT OR IGNORE INTO State (StateID, State_name) VALUES (3, 'New Jersey');")
cursor.execute("INSERT OR IGNORE INTO County (CountyID, StateID, County_Name) VALUES (7, 3, 'Camden');")
conn.commit()

###Bucket name for sectors
bucketName='camden-county-sectors'
sampleDistance=50 #Set sample distance.

###Screenshot output folder:
screenshotFolderName='roadScreenshots'
### Basically, as it uploads roads to a sector, extract the sector data and at the same time, update the .db file.

###sector files filenames (excel doc)
sectorDF=pd.read_csv('camdenCountyFileNamesCSV.csv')
### Clean the list: strip spaces, drop blank rows and duplicates (a duplicate would just redo the same sector).
sectorList=sectorDF['SECTORS'].dropna().astype(str).str.strip()
sectorList=sectorList[sectorList!='']
dupes=sectorList[sectorList.duplicated()].tolist()
if dupes:
    print(f'Warning: these sectors are listed more than once in the CSV and will only run once: {dupes}')
sectorList=sectorList.drop_duplicates().reset_index(drop=True)
### will now have a dataframe ready to go for sector reads.  Once read, index through and then run each of them through Cris' screenshot grabber.

finished=set()
if SKIP_FINISHED and os.path.exists(FINISHED_LOG):
    with open(FINISHED_LOG) as f:
        finished={line.strip() for line in f if line.strip()}

###Set Up Client
s3Client=boto3.client(service_name='s3',endpoint_url=f'https://{R2AcctID}.r2.cloudflarestorage.com',aws_access_key_id=accessIDKey,aws_secret_access_key=accessIDSecret,config=Config(signature_version="s3v4"))

###Main loop (for all of them in the dataframe, grab name and pull from cloudflare.  Extract all .txt files and write them to another file.
### At the same time, update the database to have those specific data within them.
###Object key is subject to change; need to have a csv file.

failedSectors=[] ###(sector file, error) for every sector that didn't finish, written to failedSectors.csv at the end
sectorsRun=0

### Now runs for all i.  Keep in temporary memory
for i in range(len(sectorList)):
    objectKey=sectorList.iloc[i] ###Get the sector name
    sectorName=sector_from_path(objectKey) ### "CC_1H.tif" -> "CC_1H"

    if objectKey in finished:
        print(f'Skipping {objectKey} (already in {FINISHED_LOG})')
        continue
    if MAX_SECTORS is not None and sectorsRun>=MAX_SECTORS:
        break
    sectorsRun+=1

    ### Sector/Road IDs are built from the sector NAME (not the CSV row number), so they never collide or
    ### change when the CSV is reordered or a shorter CSV (e.g. failedSectors.csv) is run.
    currentSectorID=f"SEC-{sectorName}" ###Create text-based string key for sector data.
    tempDir=None
    boxes=[]
    print(f'\n=== [{i+1}/{len(sectorList)}] {objectKey} ({currentSectorID}) ===')
    try:
        print('Downloading image from R2...')
        response=s3Client.get_object(Bucket=bucketName, Key=objectKey)

        ###Read raw binary data into memory
        imageBytes=response['Body'].read()

        with MemoryFile(imageBytes) as memfile:
            with memfile.open() as ds:
                ### (Pillow was used here before only to print the size, but it can't read every GeoTIFF layout
                ### and would fail the whole sector. rasterio reads them all.)
                print(f'Successfully loaded image! Size: ({ds.width}, {ds.height}), bands: {ds.count}, CRS: {ds.crs}')
                width,height=ds.width,ds.height
                bounds=ds.bounds ###Get bounds for database entry.

                ### Clear out any earlier run of this sector, then insert it FRESH.
                deleteSector(sectorName)
                cursor.execute('''
                    INSERT INTO Sector (
                        SectorID, CountyID, Sector_Name,
                        Sector_Uright_Lat, Sector_Uright_Long,
                        Sector_Lleft_Lat, Sector_Lleft_Long
                    ) VALUES (?, ?, ?, ?, ?, ?, ?);
                ''', (currentSectorID, 7, sectorName, bounds.top, bounds.right, bounds.bottom, bounds.left)) ### Note here, change 7 to ref a variable if we expand beyond camden county.

                ###Download roads and call the open-memory dataset to Don's code
                print('Downloading roads from OSM')
                roadsDF,transform=fetchRoads(ds.name, ds.transform) ###Don's code opens by path; ds.name is the in-memory file's path.

                print(f'Found {len(roadsDF)} named roads')
                ### Use roadsDF to then save each of the roads to the database
                ### roadsDF has only the name and the length in feet.  This will be uploaded to the roads SQL DB.  SectorID will be the i value.  RoadID will be the j value.  RoadName is the road name.  Elim Road Type.
                ###

                ### from this, you can then do the segments data, which will be where the segment ID is linked to a counter, roadID is the previous j value.  len no longer a thing.  photofile is gonna be the new cloudflare file loc.

                usedRoadFileNames=set() ### Windows file names ignore upper/lower case, so compare lowercased.
                for j in range(len(roadsDF)):
                    roadName=roadsDF.loc[j,'name']
                    currentRoadID=f'RD-{sectorName}-{j}'
                    cursor.execute("""
                        INSERT INTO Road (RoadID, SectorID, Road_Name)
                        VALUES (?, ?, ?);
                    """, (currentRoadID, currentSectorID, roadName))

                    ### File-name part for this road. If two different road names clean up to the same file name
                    ### (e.g. "Main St" / "MAIN ST", or "A/B" / "A-B"), add the road number so pictures never overwrite each other.
                    road=safe_road_name(roadName)
                    if road.lower() in usedRoadFileNames:
                        road=f'{road}_{j}'
                    usedRoadFileNames.add(road.lower())

                    points=sampleIntervals(roadsDF.loc[j,'geometry'],sampleDistance)
                    roadBoxes=sampleScreenshotCoordinates(points,sampleDistance,transform,sectorName,roadName,width,height)
                    ###Update Roads Table SectorID=i, roadID=j, RoadName=road name, no more road type.

                    ###loop through each segment box and then enter the data into the database.
                    for box in roadBoxes:
                        segmentID=box['intervalNum'] ###Same number as the screenshot file; restarts at 0 for each road.
                        screenshotName=f"{sectorName}_{road}_{segmentID:03d}.png" ###e.g. CC_1H_Burlington_Pike_000.png
                        box['fileName']=screenshotName ###Cris' code saves the picture under exactly this name.
                        cloudflareLoc=f"camden-county-street-images/{screenshotName}" ###Don's full Cloudflare location (bucket + file).

                        cursor.execute('''
                            INSERT INTO Segments (SegmentID, RoadID, photo_file)
                            VALUES (?,?,?);
                        ''', (segmentID,currentRoadID,cloudflareLoc))
                    boxes+=roadBoxes

                print(f'Found {len(boxes)} boxes.')

            ###before running the actual screenshot program, run through each segment for each road and upload accordingly.
            ### intervalNum=segmentID, roadID=the previous roadIDs (link through roadName), photo mfile is the actual cloudflare genuine location.  It will be camden-county-street-images/screenshotName.
            conn.commit()
            print(f"Database successfully updated for Sector {currentSectorID}")
        ###Now actually do all of the screenshots.
        if boxes:
            print('Starting screenshots in 3 seconds, DO NOT TOUCH THE MOUSE.  "Esc" key stops it from running.')
            time.sleep(3)
            ###Cris' autoclicker needs a real file on disk. Save it in a private temp folder (never next to your own
            ###files) so the cleanup below can only ever delete the copy this script downloaded.
            tempDir=tempfile.mkdtemp(prefix='navigator_')
            localTiff=os.path.join(tempDir, os.path.basename(objectKey))
            with open(localTiff,'wb') as f:
                f.write(imageBytes)
            connect_sector_direct.screenshot_boxes(localTiff,boxes) ###No need to save these individually since Cris' program automatically uploads them all.
        else:
            print('No bounding boxes found to process for this sector.')

        if autoclicker.stopped["esc"]:
            failedSectors.append((objectKey, 'stopped with Esc before all screenshots were taken'))
        elif objectKey not in finished:
            with open(FINISHED_LOG,'a') as f:
                f.write(objectKey+'\n')
            finished.add(objectKey)

    except Exception as e:
        print(f"Error: {e}")
        conn.rollback() ### Rollback any partial data additions should they occur under any conditions where data entry is not completed.
        failedSectors.append((objectKey, str(e)))
    finally:
        ### Each sector .tif is ~250 MB; delete the temp copy so 300 sectors don't fill the disk.
        if tempDir:
            shutil.rmtree(tempDir, ignore_errors=True)

    ### If Esc was pressed during the screenshots, stop the whole run (not just this sector).
    if autoclicker.stopped["esc"]:
        print(f"Stopped with Esc during Sector {currentSectorID}. Later sectors were not run.")
        break

conn.close() ###Close down the sqlite3 connection.

### Summary: which sectors failed (re-run just these by putting them in the CSV)
if failedSectors:
    pd.DataFrame(failedSectors, columns=['SECTORS','error']).to_csv(FAILED_LOG, index=False)
    print(f'\n{len(failedSectors)} sector(s) failed, listed in {FAILED_LOG}:')
    for name, err in failedSectors:
        print(f'  {name}: {err}')
else:
    print(f'\nAll {sectorsRun} sector(s) finished without errors.')





















