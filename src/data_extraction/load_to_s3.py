import boto3
import os

def load_data_to_s3(file_path, bucket_name, s3_key):
    s3 = boto3.client('s3', region_name=os.environ['AWS_REGION'])

    try:
        s3.upload_file(file_path, bucket_name, s3_key)
        print(f"File uploaded successfully to s3://{bucket_name}/{s3_key}")
    except Exception as e:
        print(f"Error uploading file to S3: {e}")
        raise

# Example usage
if __name__ == "__main__":
    file_path = "data/shipping_data.csv"
    bucket_name = os.environ['S3_BUCKET']
    s3_key = "shipping_data/shipping_data.csv"
    load_data_to_s3(file_path, bucket_name, s3_key)
