import os
import csv
import json
import boto3
import pg8000
from io import StringIO

# Fetch environment variables
RDS_HOST = os.environ['RDS_HOST']
RDS_PORT = int(os.environ['RDS_PORT'])
RDS_USER = os.environ['RDS_USER']
RDS_PASSWORD = os.environ['RDS_PASSWORD']
RDS_DB = os.environ['RDS_DB']
S3_BUCKET = os.environ['S3_BUCKET']
AWS_REGION = os.environ['AWS_REGION']

# Initialize AWS clients
s3_client = boto3.client('s3', region_name=AWS_REGION)
dynamodb_client = boto3.resource('dynamodb', region_name=AWS_REGION)

def extract_from_rds(query):
    """Extract data from RDS."""
    try:
        connection = pg8000.connect(
            host=RDS_HOST,
            port=RDS_PORT,
            user=RDS_USER,
            password=RDS_PASSWORD,
            database=RDS_DB
        )
        print("Connected to RDS successfully.")

        with connection.cursor() as cursor:
            cursor.execute(query)
            # Fetch column names and rows
            column_names = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            return column_names, rows
    except Exception as e:
        print(f"Error connecting to RDS: {e}")
        raise
    finally:
        if connection:
            connection.close()

def extract_from_dynamodb(table_name):
    """Extract data from DynamoDB."""
    try:
        table = dynamodb_client.Table(table_name)
        response = table.scan()
        return response['Items']
    except Exception as e:
        print(f"Error scanning DynamoDB table {table_name}: {e}")
        raise

def save_to_s3_as_csv(data, headers, file_name):
    """Save data as CSV to S3."""
    try:
        # Use StringIO to create an in-memory CSV file
        csv_buffer = StringIO()
        csv_writer = csv.writer(csv_buffer)

        # Write headers and rows
        csv_writer.writerow(headers)
        csv_writer.writerows(data)

        # Upload CSV to S3
        s3_client.put_object(Bucket=S3_BUCKET, Key=file_name, Body=csv_buffer.getvalue())
        print(f"CSV file {file_name} uploaded successfully to S3 bucket {S3_BUCKET}.")
    except Exception as e:
        print(f"Error uploading CSV to S3: {e}")
        raise

def save_dynamodb_to_s3_as_csv(data, file_name):
    """Save DynamoDB data as CSV to S3."""
    try:
        if not data:
            print(f"No data found in DynamoDB table for {file_name}")
            return

        # Extract headers and rows
        headers = list(data[0].keys())
        rows = [list(item.values()) for item in data]

        save_to_s3_as_csv(rows, headers, file_name)
    except Exception as e:
        print(f"Error processing DynamoDB data: {e}")
        raise

def lambda_handler(event, context):
    try:
        # Query RDS and save as CSV
        query = "SELECT * FROM customers LIMIT 1000;"
        headers, rds_data = extract_from_rds(query)
        save_to_s3_as_csv(rds_data, headers, "rds_data/customers.csv")

        # Query DynamoDB and save as CSV
        dynamodb_table = "Inventory"
        dynamodb_data = extract_from_dynamodb(dynamodb_table)
        save_dynamodb_to_s3_as_csv(dynamodb_data, "Inventory/inventory_data.csv")

        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "Data extraction and upload as CSV successful!"
            })
        }
    except Exception as e:
        print(f"Error in Lambda execution: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({
                "message": f"Error occurred: {e}"
            })
        }
