import numpy as np
import matplotlib.pyplot as plt
from skimage import io,morphology,exposure,data,color,feature,img_as_float, filters, restoration
from skimage.filters import median
from skimage.morphology import disk

def process_road_algorithm_Canny(imageName, road_radius=8):
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
    edges=feature.canny(smoothedImage,sigma=0.8,low_threshold=0.06,high_threshold=0.1)

    edgeDetected=(edges*255).astype(np.uint8)
    
    return edgeDetected      
### Zum Beispiel
=skeleton_img = process_road_algorithm_Canny("sampleimage_closetohome.tif", road_radius=10)

plt.imshow(skeleton_img, cmap='gray')
plt.show()
