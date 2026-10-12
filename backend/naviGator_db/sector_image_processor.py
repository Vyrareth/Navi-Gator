### Don Frenzel - Image Processing via scikit image ###
### Identifies features such as roads in the image

import os
import math
import numpy as np
import skimage as ski
from skimage import io, exposure, filters, morphology, color, restoration
from skimage.morphology import disk,binary_closing
import matplotlib.pyplot as plt


###Import the image_name & convert to matrix datatype
### Note: comes prenormalized, 0=Black, 1=white; range in pixels in-between
###       5000x5000, so fairly large to process.  Processing time can be negligble, though.  

###Process image processing:
imageName="sampleimage_closetohome.tif"

###Create a function to do this for the sake of organization.  Input is image, output is image.  
def basicRoadProcessing(imageName):
    bwimg=io.imread(imageName,as_gray=True)
    claheImg=exposure.equalize_adapthist(bwimg,clip_limit=0.03) #clahe 
    #invert the image, then smooth with gaussian
    invertedImg=1.0-claheImg 
    smoothed = filters.gaussian(invertedImg, sigma=12)

    #black_tophat to isolate the dark linear features (roads)
    footprint = morphology.footprint_rectangle((17,17)) #rough pixel width of roads
    blackTophat = morphology.black_tophat(smoothed, footprint)

    # Subtracting the blackhat response deepens the contrast of the roads
    highlightedRoads = invertedImg - blackTophat
    highlightedRoads = np.clip(highlightedRoads, 0.0, 1.0)

    #increase blackpoint to better 
    blackpoint=np.percentile(highlightedRoads,50) #def percentile for below to turn to black.  
    contrastImg=exposure.rescale_intensity(highlightedRoads,in_range=(blackpoint,1.0),out_range=(0.0,1.0)) #rescales the intensity to turn it black.

    return contrastImg

##What I need to do is find the threshold for similarity; print subset of image.
##Note, values closer to zero will be black; closer to 1 will be white

##identify long-run pixels of pure black, map it, shoot coordinates for that unique road identifier to a dataframe, and also its general bounds (i.e. how many pixels away from it can
## you go without running into noise), which should result in the upper and lower edges for every column of pixels contained, which are also convenient for centering screenshots.

## method used for this will either be BFS or DFS, since every node will eventually be visited.
## determine starting point.  
#search for long strings of zeroes, have conditions regarding the stretch; check reqs doc, wrote it down.  
randomSeed=np.random.default_rng()

###choose a random pixel within the matrix
def findRandomBlackPixel(matrix,rng):
    pixelFound=0
    ###continually checks if the condition is not fulfilled
    while(pixelFound==0):
        randomRow=rng.integers(0,matrix.shape[0])
        randomCol=rng.integers(0,matrix.shape[1])
        pixelVal=matrix[randomCol,randomRow]
        if(pixelVal==0.0):
            pixelFound=1
            return (randomCol,randomRow) #Col (x), and Row (y) to keep in line with standard notation.                 
    
### explore outwards until an end is met by all pixels.  NOTE: if end is at 5000 or 0, then note that as an edge of the graph.  
def breadthCheck(matrix,pixel):
    curPixelCol,curPixelRow = pixel #def current pixel
    terminalPoints=0 #track number of terminations
    terminalPositions={} #track terminal positions of each n.  

    ###store as dictionary for modification and transfer ease.  While position stores the current position of the pixel at hand, direction stores the movement constants.  
    curMovement={
        'n1':{'position':[curPixelCol,curPixelRow+1],'direction':[0,1]},
        'n2':{'position':[curPixelCol+1,curPixelRow],'direction':[1,0]},
        'n3':{'position':[curPixelCol,curPixelRow-1],'direction':[0,-1]},
        'n4':{'position':[curPixelCol,curPixelRow-1],'direction':[-1,0]},
        'n5':{'position':[curPixelCol+1,curPixelRow+1],'direction':[1,1]},
        'n6':{'position':[curPixelCol-1,curPixelRow+1],'direction':[-1,1]},
        'n7':{'position':[curPixelCol+1,curPixelRow-1],'direction':[1,-1]},
        'n8':{'position':[curPixelCol-1,curPixelRow-1],'direction':[-1,-1]}
    }

    activePixels=list(curMovement.keys()) #store active keys

    ###main loop body; move each out by one until it hits a wall.  
    while terminalPoints<8:
        nextActivePixels=[] #store the new list of active pixels

        ###Run through active pixels so long as they haven't reached a terminating point.  
        for pixel in activePixels:
            currPixel=curMovement[pixel]
            
            ###increase the current position by its correct amount (widest applicable)
            currPixel['position'][0]+=currPixel['direction'][0]
            currPixel['position'][1]+=currPixel['direction'][1]

            ###track the current column and current row
            curCol=currPixel['position'][0]
            curRow=currPixel['position'][1]

            if -1<curCol<5001 and -1<curRow<5001:
                if matrix[curCol,curRow]!=0.0: #check if it's a nonblack pixel
                    #if so, ensure that the terminal positions are properly entered.  
                    terminalPositions[pixel]=[curCol,curRow]
                    terminalPoints+=1
                else:
                    nextActivePixels.append(pixel)
        activePixels=nextActivePixels

    #at this point now, we have all of the terminal points.  We now need to measure their distance from the origin
    terminalPositions=dict(sorted(terminalPositions.items()))

    #next we basically want to check their distance each from the origin point to determine the size of the area (and general shape)
    #because, there is a general need to know the shape so that it isn't a small, disconnected blob.
    #additionally, there are some ghost darks from trees that can be addressed in later updates.  
    distFromOrigin={'n1':None,'n2':None,'n3':None,'n4':None,'n5':None,'n6':None,'n7':None,'n8':None}
    originPixel=[curPixelCol,curPixelRow]

    ##Here it just gets the Euclidean Distance between the origin and the points.  
    for pixel in terminalPositions:
        currPixel=curMovement[pixel]
        pixelC=currPixel['position'][0]
        pixelR=currPixel['position'][1]
        farPixel=[pixelC,pixelR]
        #calculate Euclidean Distance (Norm)
        distance=math.dist(originPixel,farPixel)
        #now enter that into the distFromOrigin
        distFromOrigin[pixel]=distance

    ###print out some of them for funsies.  
    print(terminalPositions)
    print(terminalPoints)
    print(distFromOrigin)



###For testing's sake
contrastImg=basicRoadProcessing(imageName)

col,row=findRandomBlackPixel(contrastImg,randomSeed)
pixel=(col,row)
breadthCheck(contrastImg,pixel)


##for show
plt.imshow(contrastImg,cmap='gray') 
plt.show()
