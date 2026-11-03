###Navi-Gator Script to retrieve files.
import io
import sqlite3
import boto3
import pandas as pd
from botocore.config import Config
from PIL import Image

###import code from Cris
from connect_sector_direct import (sampleIntervals, sampleScreenshotCoordinates, screenshot_boxes, sector_from_path)
from sectorCoordinateProcessor import roadsFromSector

###For API Access regarding Cloudflare pulling/uploads.
R2AcctID= ### Change this to yours.  
accessIDKey= ### Change this to yours
accessIDSecret= ### Change this to yours
jurisSpecEndPoint= ###Change this to yours

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
sectorList=sectorDF['SECTORS'] #grab only the sectors.  
### will now have a dataframe ready to go for sector reads.  Once read, index through and then run each of them through Cris' screenshot grabber.

###Set Up Client
s3Client=boto3.client(service_name='s3',endpoint_url=f'https://{R2AcctID}.r2.cloudflarestorage.com',aws_access_key_id=accessIDKey,aws_secret_access_key=accessIDSecret,config=Config(signature_version="s3v4"))

###Main loop (for all of them in the dataframe, grab name and pull from cloudflare.  Extract all .txt files and write them to another file.
### At the same time, update the database to have those specific data within them.
###Object key is subject to change; need to have a xlsx file.


### Define Database Structure



### Now runs for all i.  Keep in temporary memory
for i in range(len(sectorList)):
    objectKey=sectorList.iloc[i] ###Get the sector name

    currentSectorID = f"SEC-{i}" ###Create text-based string key for sector data.  
    try:
        print('Downloading image from R2...')
        response=s3Client.get_object(Bucket=bucketName, Key=objectKey)
        
        ###Read raw binary data into memory
        imageBytes=response['Body'].read()
        
        ### Open the TIFF file using Pillow
        img=Image.open(io.BytesIO(image_bytes))
        print(f'Successfully loaded image! Format: {img.format}, Size: {img.size}')
        
        ### Run Cris' extension of program to retrieve all instances of that road and put them into a folder.
        sectorName=sector_from_path(objectKey)
        
        with MemoryFile(imageBytes) as memfile:
            with memfile.open() as ds:
                width,height=ds.width,ds.height
                bounds=ds.bounds ###Get bounds for database entry.  

                ###Inserts the new sector into the database FRESH.  
                cursor.execute('''
                    INSERT OR REPLACE INTO Sector (
                        SectorID, CountyID, Sector_Name, 
                        Sector_Uright_Lat, Sector_Uright_Long, 
                        Sector_Lleft_Lat, Sector_Lleft_Long
                    ) VALUES (?, ?, ?, ?, ?, ?, ?);
                ''', (currentSectorID, 7, sectorName, bounds.top, bounds.right, bounds.bottom, bounds.left)) ### Note here, change 7 to ref a variable if we expand beyond camden county.  
                
                ###Download roads and call the open-memory dataset to Don's code
                print('Downloading roads from OSM')
                roadsDF,transform=roadsFromSector(ds)

                print(f'Found {len(roadsDF)} named roads')
                ### Use roadsDF to then save each of the roads to the database
                ### roadsDF has only the name and the length in feet.  This will be uploaded to the roads SQL DB.  SectorID will be the i value.  RoadID will be the j value.  RoadName is the road name.  Elim Road Type.
                ###

                ### from this, you can then do the segments data, which will be where the segment ID is linked to a counter, roadID is the previous j value.  len no longer a thing.  photofile is gonna be the new cloudflare file loc.
            
                
                boxes=[]
                segmentCounter=1
                for j in range(len(roadsDF)):
                    roadName=roadsDF.loc[j,'name']
                    currentRoadID=f'RD-{i}-{j}'
                    cursor.execute("""
                        INSERT OR REPLACE INTO Road (RoadID, SectorID, Road_Name)
                        VALUES (?, ?, ?, ?);
                    """, (currentRoadID, currentSectorID, roadName))
                    
                    points=sampleIntervals(roadsDF.loc[j,'geometry'],sampleDistance)
                    roadBoxes=sampleScreenshotCoordinates(points,sampleDistance,transform,sectorName,roadsDF.loc[j,"name"],width,height)
                    boxes+=roadBoxes
                    ###Update Roads Table SectorID=i, roadID=j, RoadName=road name, no more road type.  

                ###loop through each segment box and then enter the data into the database.  
                for box in roadBoxes:
                    screenshotName=f"{sectorName}-{roadName.replace(' ','_')}-{segmentCounter}.jpg"
                    cloudflareLoc=f"camden-county-street-images/{screenshot_name}"

                    cursor.execute('''
                        INSERT OR REPLACE INTO Segments (SegmentID, RoadID, photo_file)
                        VALUES (?,?,?);
                    '''), (segmentCounter,currentRoadID,cloudflareLoc)
                    segmentCounter+=1 ###increase segment counter after; resets to 1 upon new road.  

                print(f'Found {len(boxes)} boxes.')

            ###before running the actual screenshot program, run through each segment for each road and upload accordingly.
            ### intervalNum=segmentID, roadID=the previous roadIDs (link through roadName), photofile is the actual cloudflare genuine location.  It will be camden-county-street-images/screenshotName.
            conn.commit()
            print(f"Database successfully updated for Sector {currentSectorID}")
        ###Now actually do all of the screenshots.
            
        if boxes:
            print('Starting screenshots in 3 seconds, DO NOT TOUCH THE MOUSE.  "Esc" key stops it from running.')
            screenshot_boxes(objectKey,boxes) ###No need to save these individually since Cris' program automatically uploads them all.  
        else:
            print('No bounding boxes found to process for this sector.')
                
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback() ### Rollback any partial data additions should they occur under any conditions where data entry is not completed.

    ### Now modify to have the actual sql db uploads.  

    break ###Remove later, this limits it to a single index.

conn.close() ###Close down the sqlite3 connection.  





















