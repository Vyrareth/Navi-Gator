import numpy as np
import cv2 #for Hough Transform only
import matplotlib.pyplot as plt
from skimage import io,morphology,exposure,data,color,feature,img_as_float, filters, restoration
from skimage.filters import median
from skimage.morphology import disk

from scipy.ndimage import distance_transform_edt, maximum_filter
from scipy.spatial import KDTree

###Algorithm for Edge Detection and general first run filtering. 
def process_road_algorithm_Canny(imageName):
    ###FIrst perform edge detection using either sobel or canny
    bwimage=io.imread(imageName,as_gray=True)
    ##step 1: invert the image
    invertedImage=1.0-bwimage
    
    #blackpoint=np.percentile(invertedImage,12) #def percentile for below to turn to black.  
    #contrastImg=exposure.rescale_intensity(invertedImage,in_range=(blackpoint,1.0),out_range=(0.0,1.0)) #rescales the intensity to turn it black.
    #equalizedImage = exposure.equalize_adapthist(invertedImage, kernel_size=[64,64], clip_limit=0.008)

    ###double median filter helps avoid pitfalls. 
    medianFiltered=median(invertedImage, disk(2))
    medianFiltered2=median(medianFiltered,disk(2))

    ###try a median filter
    blackpoint=np.percentile(medianFiltered2,18) #def percentile for below to turn to black.  
    contrastMF=exposure.rescale_intensity(medianFiltered2,in_range=(blackpoint,1.0),out_range=(0.0,1.0))

    ###before smoothing, find a way to darken obstructions
    smoothedImage=filters.gaussian(contrastMF, sigma=3.0)
    edges=feature.canny(smoothedImage,sigma=0.8,low_threshold=0.04,high_threshold=0.08) #prev 0.06-0.1

    edgeDetected=(edges*255).astype(np.uint8)
    
    return edgeDetected

###Perform the reference circle calculation step & direction.  
def extractCentralPixels(edgeDetected):
    binaryEdges=(edgeDetected>0) #grab only the edge lines

    ###Calculate ref. circles using Euclidean Distance Transform, which computes distance to the nearest zero.  Using the ~ operator guarantees that edges are 0 and background is 1
    ### so that we find the distance from every pixel in the background to every edge point it's nearest to.  
    referenceCircleRadius=distance_transform_edt(~binaryEdges)

    ###Locate the central pixels;
    localMax=maximum_filter(referenceCircleRadius,size=3)

    ###A pixel is considered central if its radius matches the 3x3 local maximum and has valid width.
    central=(referenceCircleRadius==localMax) & (referenceCircleRadius>0)

    ###extract coordinates and radii of the centralmost pixels
    yCords,xCords=np.where(central)
    radii=referenceCircleRadius[yCords,xCords]
    
    ###create an array of central points. 

    points=np.array(list(zip(xCords,yCords))) #should still work
    ###for function output.  Should be the cords,radius, and direction of the central pixel.  Optimized with KD tree for better spatial lookups
    tree=KDTree(points)
    centralPixelData=[]

    ###If there are any central points, go through them, calculate the radisu, then the distances using euclidean norm, then find all pixels within that distance.  
    ###Then once you have those points, extract all points within that group from points into groupPoints.  From there, the direction is determined by
    ###taking the distance of the central point, as in all of the points in that grouping subtracting the mean of their distances from one another (for a centroid), which you
    ###then get by taking the direction by taking the singular value decomposition, in which the V^T matrix determines the direction.

    ###NOTE: OPTIMIZE THIS
    for i, (x,y) in enumerate(points):
        radius=radii[i]
        neighborInds=tree.query_ball_point([x,y],radius)
        groupPoints=points[neighborInds]
        direction=np.array([0.0,0.0])
        if len(groupPoints)>2:
            centroid=groupPoints-np.mean(groupPoints,axis=0) #calculate central point and utilize it as the centroid.  
            _,_,VT=np.linalg.svd(centroid) #use SVD to evaluate centroid direction
            direction=VT[0]
            ###Output data as the coordinate of the central point, its radius, and its direction.  
        centralPixelData.append({'cord':(x,y),'radius':radius,'direction':direction})
    return centralPixelData

###The next step in the process, segmentation
def segmentationProcess(centralPixelData,minRoadWidth=7):
    widthFiltered=[p for p in centralPixelData if p['radius']>=minRoadWidth]
    if len(widthFiltered)==0:
        print("no viable candidates found with current constraint")
        return 1

    ###If there are more than zero, eval global shape ratio.  Meaning, make sure that the shape ratio is within reasonable bounds.  
    totalCentralPixels=len(widthFiltered)
    avgRadius=np.mean([p['radius'] for p in widthFiltered])
    shapeRatio=totalCentralPixels/avgRadius
    
    ratioThresh=2.0
    if shapeRatio<ratioThresh:
        print(f"Region rejected due to the low shape ratio: {shapeRatio:.2f}")
        return 1

    print(f"Region Passed Segmentation Test with shape ratio: {shapeRatio:.2f}")
    return widthFiltered #these are the segmented candidates

### Now for the colinearity check

###NOTE ERROR
def collinearityCheck(validCandidates,imageShape):
    centralPixelCanvas=np.zeros(imageShape,dtype=np.uint8)

    for p in validCandidates:
        x,y=p['cord']
        centralPixelCanvas[y,x]=255 #mark them as white

    ###Use probabilistic Hough Transform to check Collinearity across the segements.
    lines= cv2.HoughLinesP(centralPixelCanvas,rho=1,theta=np.pi/180,threshold=20,minLineLength=50,maxLineGap=50) #8,50 we're getting somewhere

    verifiedSegments=[]
    if lines is not None:
        for line in lines:
            flatLine=np.ravel(line)
            if len(flatLine)>=4:
                x1,y1,x2,y2=flatLine[:4]
                verifiedSegments.append(((int(x1),int(y1)),(int(x2),int(y2))))

    return verifiedSegments


###Group & Optimize, second round of these, then group and reoptimize again.
def optimizeAndFilterSegments(verifiedSegments, minLength=60,maxMergeGap=15):
    '''
    cleanedSegments=[]
    for segment in verifiedSegments:
        (x1,y1),(x2,y2)=segment
        length=np.sqrt((x2-x1)**2+(y2-y1)**2)

        if length>=minLength:
            cleanedSegments.append(segment)
    '''
    ###Try with vectorized math instead
    segmentsArray=np.array(verifiedSegments)
    x1=segmentsArray[:,0,0]
    y1=segmentsArray[:,0,1]
    x2=segmentsArray[:,1,0]
    y2=segmentsArray[:,1,1]

    lengths=np.sqrt((x2-x1)**2+(y2-y1)**2)
    valid=lengths>=minLength
    filteredSegments=segmentsArray[valid]
    
    '''
    merged=True
    while merged:
        merged=False
        newSegments=[]
        while cleanedSegments:
            current=cleanedSegments.pop(0)
            (x1,y1),(x2,y2)=current

            mergedWOther=False
            for i,other in enumerate(cleanedSegments):
                (ox1,oy1),(ox2,oy2)=other

                d1=np.sqrt((x2-ox1)**2+(y2-oy1)**2)
                d2=np.sqrt((x1-ox2)**2+(y1-oy2)**2)

                if d1<maxMergeGap or d2<maxMergeGap:
                    allPoints=np.array([[x1,y1],[x2,y2],[ox1,oy1],[ox2,oy2]])
                    maxD=0
                    pa,pb=current[0],current[1]
                    for pointA in allPoints:
                        for pointB in allPoints:
                            dist=np.linalg.norm(pointA-pointB)
                            if dist>maxD:
                                maxD=dist
                                pa,pb=(pointA[0],pointA[1]),(pointB[0],pointB[1])
                    newSegments.append((pa,pb))
                    cleanedSegments.pop(i)
                    mergedWOther=True
                    merged=True
                    break
            if not mergedWOther:
                newSegments.append(current)
        cleanedSegments=newSegments
    
    return cleanedSegments
    '''
    return [((int(s[0,0]),int(s[0,1])),(int(s[1,0]),int(s[1,1]))) for s in filteredSegments]

###Roll em up into one big function
def stage1Pipeline(imageName):
    edgesIdentified=process_road_algorithm_Canny(imageName)
    centralPixelData=extractCentralPixels(edgesIdentified)
    validCands=segmentationProcess(centralPixelData)
    finalRoadSegments=collinearityCheck(validCands,edgesIdentified.shape)
    optRoadSegs=optimizeAndFilterSegments(finalRoadSegments)
    return optRoadSegs




### Zum Beispiel
originalImage="sampleimage_closetohome.tif"
optimalRoadSegments=stage1Pipeline(originalImage)



###This is for displaying the image
# Create an RGB canvas (or copy of your original image)
orig_img = cv2.imread(originalImage)
if orig_img is None:
    # Fallback if using io.imread or if it's single-channel grayscale
    gray_img = io.imread(original_image_path, as_gray=True)
    orig_img = cv2.cvtColor((gray_img * 255).astype(np.uint8), cv2.COLOR_GRAY2RGB)
else:
    orig_img = cv2.cvtColor(orig_img, cv2.COLOR_BGR2RGB)

# Draw each verified segment onto the image
for segment in optimalRoadSegments:
    pt1, pt2 = segment
    # Draw a thick green line for the road segment (adjust thickness as needed)
    cv2.line(orig_img, pt1, pt2, color=(0, 255, 0), thickness=2)

# Display using matplotlib
plt.figure(figsize=(12, 12))
plt.imshow(orig_img)
plt.title("Extracted Road Network Overlay")
plt.axis('off')
plt.show()

