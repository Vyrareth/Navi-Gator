###|====================================================|###
###|SATELLITE IMAGE ROAD COORDINATE FINDER 1.0          |###
###|====================================================|###

### PROGRAM WRITTEN BY DON FRENZEL

### Vers History:
### 1.0 - 20.10.2026

### =====================================================================================================================================================================================
### Desc:  This program takes the input of a sector image .tiff file and outputs a pandas df possessing all data necessary to mesh with screenshot program to display viable candidates
###        for extraction.  UL, LR positions (i.e northwestmost and southeastmost).
###        Note the pipeline function, which should be the last.  It manages all other functions, the process of which is as follows:
###        .tiff sector file input => roadsFromSector() => roadsDF => sampleIntervals() => fullPoints Dataframe => sampleScreenshotsCoordinates() => coordinate data dataframe (result)
###
###        Input into Pipeline: tiffPath (filepath), tiffSize (always 5000 by 5000), sampleDistance (how many feet between samples, default is 50).
###        Output of Pipeline: Pandas Dataframe which includes the following: SectorName, RoadName, intervalNum (per road, iterable), UL Coords (tuple), and LR Coords (tuple).

###        Also, please note that while I haven't run the pipeline function itself yet, every part of it has been run and the function is just a translation.  
### =====================================================================================================================================================================================


###Imports
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches

import cv2
import rasterio
import rasterio.transform
import geopandas as gpd
import osmnx as ox

from rasterio.features import rasterize
from pyproj import Transformer
from shapely.ops import linemerge
from pathlib import Path
from itertools import chain

###Force OSMnx to use a backup public mirror instead of the overloaded German server
###The community server 'overpass.private.coffee' or public 'overpass.openstreetmap.fr' are excellent alternatives
ox.settings.overpass_url = "https://overpass.private.coffee/api"

###Disable rate limit
ox.settings.overpass_rate_limit = False

ox.settings.max_query_area_size = 5000000000  ###Prevent req-splitting issues
ROAD_LINE_THICKNESS_PIXELS = 5 
###=======================================================================

###Function to compile a dataframe of roads present in the sector image (set output image false by default
def roadsFromSector(tiffImagePath,outputFile=False):    
    ### Grab the height, width, and geotransform matrix without loading the image itself
    with rasterio.open(tiffImagePath) as dataset:
        westNative,southNative,eastNative,northNative=dataset.bounds
        height=dataset.height
        width=dataset.width
        transform=dataset.transform

    ### Coordinate Transformation Setup (NJ State Plane Feet to WGS84 Lat/Lng)
    njCRS="EPSG:3424" #def NJ WGS84.
    transformer=Transformer.from_crs(njCRS,"EPSG:4326",always_xy=True)

    minLon,minLat=transformer.transform(westNative,southNative)
    maxLon,maxLat = transformer.transform(eastNative,northNative)

    #### Spatial alignment for OSMnx 2.0+ format: (left, bottom, right, top)
    west=minLon
    east=maxLon
    south=minLat
    north=maxLat

    ### def bounding box to fetch the applicable road vectors.  
    bbox=(west, south, east, north)

    ### grab features from the bounding box coordinates in OSM
    roadsGeoDF=ox.features_from_bbox(bbox=bbox, tags={"highway": True})

    ### reconv vectors
    roadsGeoDF=roadsGeoDF.to_crs(njCRS)

    ### Get the road names and make entries for data not there
    roadsGeoDF=roadsGeoDF[roadsGeoDF.geometry.type.isin(['LineString', 'MultiLineString'])]
    if 'name' not in roadsGeoDF.columns:
        roadsGeoDF['name'] = "Unnamed Road"
    roadsGeoDF['name'] = roadsGeoDF['name'].fillna("Unnamed Road")

    ###Aggregate lines by name and combine geometric native lengths
    dissolvedGeoDF=roadsGeoDF.dissolve(by='name', as_index=False)

    ###Fialize the dataframe as a copy of the geometry and name, then assign length to the geometry metric (length) to the df and sort by length
    unsortedDataframe=dissolvedGeoDF[['name', 'geometry']].copy()
    unsortedDataframe['total_length_feet']=unsortedDataframe['geometry'].length
    sortedDataframe=unsortedDataframe.sort_values(by='total_length_feet', ascending=False).reset_index(drop=True)

    ###Note, unnamed in this case is the length of all extra roads, shoulder, unnamed paths that aren't registered as streets, etc.  Remove them for now.  Can be added later.  
    fullDataframe=sortedDataframe[sortedDataframe['name']!='Unnamed Road'].reset_index(drop=True)
    dataTransform=dataset.transform
    return fullDataframe, dataTransform


### Interval samples (Add and subtract avg roadway width from height and subtract 50 for Left Upper Bound, add 50 for Right lower bound.

def sampleIntervals(roadGeometry,stepsInFeet=50): #set default to 50, but generally will be reflective of whatever is best for the CNN
    ### Check first if the intervals are empty or not; if so, quit.  Won't be but better to be safe lol.
    if roadGeometry.is_empty:
        return []

    ### Check if its a multilinestring, which is what it sounds like.  If so, convert.  If it doesn't convert, try, try again.  
    if roadGeometry.geom_type=='MultiLineString':
        roadGeometry=linemerge(roadGeometry)
        if roadGeometry.geom_type=='MultiLineString':
            roadGeometry=max(list(roadGeometry.geoms),key=lambda l: l.length)

    ### Get the total length of the road
    totalLength=roadGeometry.length

    ###Array of distances along the road spaced by the specified interval
    distances=np.arange(0,totalLength,stepsInFeet)

    if distances[-1]<totalLength:
        distances=np.append(distances,totalLength)

    ###Interpolate the dataset to grav tge exact x and y coordinates along a road at that specific distance interval.  
    sampledPoints=[]
    changeOverStep=1.0 #small 1 foot step change to determine the direction of propagation
    for d in distances:
        pointInit=roadGeometry.interpolate(d)
        lookahead=d+changeOverStep if (d+changeOverStep)<=totalLength else d-changeOverStep #check behind if at the absolute end.  

        interpLooka=roadGeometry.interpolate(lookahead)

        if (d+changeOverStep<=totalLength):
            dx=interpLooka.x-pointInit.x
            dy=interpLooka.y-pointInit.y
        else:
            dx=pointInit.x-interpLooka.x
            dy=pointInit.y-interpLooka.y

        ###Calculate angle of propagation
        propAngle=(np.degrees(np.arctan2(dx,dy))+360)%360 ### 0-360 degrees, 0=North, clockwise.  NESW direction.  

        
        sampledPoints.append({'x':pointInit.x,'y':pointInit.y,'distanceFromStarting':d,'propAngle':propAngle})

    ###Now take sample points and convert it back into actual pixel coordinates
    return sampledPoints

### Now for each output of points in samplePoints, manipulate so that the coordinates are exactly as follows
def sampleScreenshotCoordinates(samplePoints,sampleDistance,datasetTransform,sectorName,roadName,imageWidth,imageHeight):
    feetPerPixel=datasetTransform[0]

    windowSizePixels=int(sampleDistance/feetPerPixel) ###Sliding window in size pixels

    if (windowSizePixels%2)!=0:
        windowSizePixels+=1
        
    halfWind=windowSizePixels//2
    ###for each value in samplePoints\
    curPointIndex=0
    screenshotCoordinates=[] #ret
    for i,point in enumerate(samplePoints):
        xC=point['x']
        yC=point['y']
        distanceFromStartC=point['distanceFromStarting'] #find whether it is the first point; if so, the create special case for first and last
        propAngleC=point['propAngle']

        ###convert into pixels
        r,c=rasterio.transform.rowcol(datasetTransform,xC,yC)
        rCenter,cCenter=int(r),int(c)

        ULcol=cCenter-halfWind
        ULrow=rCenter-halfWind
        LRcol=ULcol+windowSizePixels
        LRrow=ULrow+windowSizePixels

        ###Filter coordinates not within the actual range/scope of the .tiff image
        if not (0<=ULcol and 0<=ULrow and LRcol<=imageWidth and LRrow<=imageHeight):  
            continue #skip the other steps if not satisfactory
        
        screenshotCoordinates.append({'SectorName':sectorName,'RoadName':roadName,'intervalNum':curPointIndex,'ULCoords':(ULcol,ULrow),'LRCoords':(LRcol,LRrow)})
        curPointIndex+=1

    return screenshotCoordinates

### Create a pipeline for grabbing all viable road coordinates in an area. ###Tiff name is the name of the Sector. 
def roadGrabPipe(tiffPath,tiffSize,sampleDistance=50):
    ###Grab the sector name from the tiffName

    ##tiffName is the last bit of the file
    cutTiff=tiffPath.split("/")[-1] #grab last file value in extension    
    sectorName=cutTiff.split(".")[0] # "CC_1E"
    
    ###Create a dataframe for output
    allCoords=[] #nested list which contains all lists.  

    ###Get the roads of the sector's dataframe
    sectorRoadsDF,dataTransform=roadsFromSector(tiffPath,outputFile=False)
    
    ###Get all of these into a pipeline
    for i in len(sectorRoadsDF):
        roadGeometries=sectorRoadsDF.loc[i,'geometry'] 
        roadName=sectorRoadsDF.loc[i,'name']
        
        ###compile all sample points for that specific road.
        samplePoints=sampleIntervals(roadGeometries,sampleDistance) #now that i have sample points, create a function that essentially fills in the gaps
        ###grab all window coordinates for that road
        windowCoords=sampleScreenshotCoordinates(samplePoints, sampleDistance, dataTransform,sectorName,roadName,tiffSize,tiffSize)
        allCoords.append(windowCoords)

    ### Flatten the data into a single list of dictionaries
    flattenedData=list(chain.from_interable(allCoords))
    
    ### Make that flattened data into a dict
    allRoadData=pd.DataFrame(flattenedData)

    return flattenedData
    
