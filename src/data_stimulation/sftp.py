import pandas as pd
from faker import Faker
import random
import os
import boto3
from botocore.exceptions import NoCredentialError

fake = Faker()

#AWS S3 Bucket Details
S3_Bucket_Name = "retail-shipping-address-dump-01082025"
S3_FILE_PREFIX = "shipping_data/"
AWS_REGION = "us-west-2"
AWS_ACCESS_KEY = "XXXXX"
AWS_SECRET_KEY = "XXXXXXXXX"

# Define the path to the "data" folder outside the "src" folder
project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
data_folder = os.path.join(project_dir, 'data')

# Ensure the "data" folder exists
os.makedirs(data_folder, exist_ok=True)

# Generate Shipping Data
shipping_data = pd.DataFrame([
    {
        "order_id": fake.uuid4(),
        "customer_id": random.randint(1, 100),
        "shipping_address": fake.address(),
        "status": random.choice(["Shipped", "In Transit", "Delivered", "Returned"]),
        "shipping_date": fake.date_between(start_date='-1y', end_date='today')
    }
    for _ in range(500)
])

# Save the CSV in the "data" folder
csv_path = os.path.join(data_folder, "shipping_data.csv")
shipping_data.to_csv(csv_path, index=False)

print(f"Shipping data saved to {csv_path}")

def upload_to_s3(file_path, bucket_name, s3_key):
    try:
        s3 = boto3.client(
            "s3",
            aws_access_key_id=AWS_ACCESS_KEY,
            aws_secret_access_key=AWS_SECRET_KEY,
            region_name=AWS_REGION
        )
    
        #Upload file to S3
        s3.upload_file(file_path, bucket_name, s3_key)
        print(f"File uploaded successfully to s3://{bucket_name}/{s3_key}")

    except NoCredentialError:
        print("AWS credentials not available.")

    except Exception as e:
        print(f"Error Uploading file to s3: {e}")

s3_key = f"{S3_FILE_PREFIX}shipping_data_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv"

upload_to_s3(csv_path, S3_Bucket_Name, s3_key)

'''
# Cleanup: Deleting the local csv file
if os.path.exists(csv_path):
    os.remove(csv_path)
    print(f"Temporary local file {csv_path} removed.")
'''