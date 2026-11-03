###Navi-Gator Script to retrieve files.
import io
import boto3
import pandas as pd
from botocore.config import Config
from PIL import Image  

###For API Access regarding Cloudflare pulling/uploads.
R2AcctID='' ### Change this to yours.  
accessIDKey='' ### Change this to yours
accessIDSecret='' ### Change this to yours
jurisSpecEndPoint=''  ###Change this to yours
bucketName='camden-county-sectors'

###sector files filenames (excel doc)
sectorDF=pd.read_csv('camdenCountyFileNamesCSV.csv')
sectorList=sectorDF['SECTORS'] #grab only the sectors.  
### will now have a dataframe ready to go for sector reads.  Once read, index through and then run each of them through Cris' screenshot grabber.

###Set Up Client


###Main loop (for all of them in the dataframe, grab name and pull from cloudflare.  Extract all .txt files and write them to another file.
### At the same time, update the database to have those specific data within them.
s3Client=boto3.client(service_name='s3',endpoint_url=f'https://{R2AcctID}.r2.cloudflarestorage.com',aws_access_key_id=accessIDKey,aws_secret_access_key=accessIDSecret,config=Config(signature_version="s3v4"))
###Object key is subject to change; need to have a xlsx file.


### Now runs for all i.  
for i in range(len(sectorList)):
    objectKey=sectorList.iloc[i] ###Get the sector name
    try:
        print("Downloading image from R2...")
        response=s3Client.get_object(Bucket=bucketName, Key=objectKey)
        
        # Read the raw binary data into memory
        image_bytes=response["Body"].read()
        
        # Open the TIFF file using Pillow
        img=Image.open(io.BytesIO(image_bytes))
        print(f"Successfully loaded image! Format: {img.format}, Size: {img.size}")
        
        # Example action: Save it locally to your machine
        # img.save("downloaded_CC_10C.tif")

    except Exception as e:
        print(f"Error: {e}")
    break ###Remove later
