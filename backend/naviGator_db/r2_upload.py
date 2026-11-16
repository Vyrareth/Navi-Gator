import os
import glob
import boto3
from botocore.config import Config

# ==================== CONFIGURATION ====================
# Replace these with your actual Cloudflare R2 credentials
ACCOUNT_ID = "7e641eadc881f6ff1bed3efd05a3fc2f"
ACCESS_KEY_ID = "10fdd6f3feac4c796d1b92bd77e74a0d"
SECRET_ACCESS_KEY = "bbecb725abfa15407bbf175e48af86f5775bc2b7fca3718e6963f9138a91a44c"
BUCKET_NAME = "camden-county-street-images"

# Path to your folder containing PNGs (use "." if the script is in the same folder)
FOLDER_PATH = r"C:\Users\jospe\Desktop\SWE\R2 database download\CC_1H" 
# =======================================================

def upload_pngs():
    # Configure the S3 client to point to Cloudflare R2
    r2_endpoint = f"https://{ACCOUNT_ID}.r2.cloudflarestorage.com"
    
    s3_client = boto3.client(
        service_name="s3",
        endpoint_url=r2_endpoint,
        aws_access_key_id=ACCESS_KEY_ID,
        aws_secret_access_key=SECRET_ACCESS_KEY,
        config=Config(signature_version="s3v4")
    )

    # Find all PNG files in the specified directory
    search_path = os.path.join(FOLDER_PATH, "*.png")
    png_files = glob.glob(search_path)

    if not png_files:
        print(f"No PNG files found in: {FOLDER_PATH}")
        return

    print(f"Found {len(png_files)} PNG files. Starting upload...")

    for file_path in png_files:
        # Get just the file name (e.g., "image1.png") to use as the R2 object key
        file_name = os.path.basename(file_path)
        
        try:
            print(f"Uploading {file_name}...", end="", flush=True)
            
            # Upload the file and set the correct content type for images
            s3_client.upload_file(
                Filename=file_path,
                Bucket=BUCKET_NAME,
                Key=file_name,
                ExtraArgs={"ContentType": "image/png"}
            )
            
            print(" ✅ Success")
        except Exception as e:
            print(f" ❌ Failed: {str(e)}")

    print("\n All uploads finished!")

if __name__ == "__main__":
    upload_pngs()
