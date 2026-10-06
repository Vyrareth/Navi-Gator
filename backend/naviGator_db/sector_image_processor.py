### Don Frenzel - Image Processing via scikit image ###
### Identifies features such as roads in the image

import os
import numpy as np
import skimage as ski
from skimage import io, exposure, filters
from skimage.morphology import disk,binary_closing
import matplotlib.pyplot as plt


###Import the image_name & convert to matrix datatype
### Note: comes prenormalized, 0=Black, 1=white; range in pixels in-between
###       5000x5000, so fairly large to process.  Processing time can be negligble, though.  

imageName="sampleimage_closetohome.tif"
bwimg=io.imread(imageName,as_gray=True)
invImg=1.0-bwimg #invert the image colors

###increase exposure for blacker blacks and lighter lights (contrast helps with ident), using clahe (Contrast-Limited Adaptive Histogram Equalization) to 
claheProcessed=exposure.equalize_adapthist(invImg, clip_limit=0.03) #, kernel_size=(32,32)
blackpoint=np.percentile(claheProcessed,40) #def percentile for below to turn to black.  
contrastImg=exposure.rescale_intensity(claheProcessed,in_range=(blackpoint,1.0),out_range=(0.0,1.0)) #rescales the intensity to turn it black.  

##What I need to do is find the threshold for similarity; print subset of image.
##Note, values closer to zero will be black; closer to 1 will be white

##identify long-run pixels of pure black, map it, shoot coordinates for that unique road identifier to a dataframe, and also its general bounds (i.e. how many pixels away from it can
## you go without running into noise), which should result in the upper and lower edges for every column of pixels contained, which are also convenient for centering screenshots.

## method used for this will either be BFS or DFS, since every node will eventually be visited.
## determine starting point.  
print(contrastImg[500:1000,500:1000])
#search for long strings of zeroes, have conditions regarding the stretch; check reqs doc, wrote it down.  


##for show
plt.imshow(contrastImg,cmap='gray') 
plt.show()
