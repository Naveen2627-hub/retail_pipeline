import os
import psycopg2
import boto3

def lambda_handler(event, context):
    # Redshift credentials
    endpoint = os.environ['REDSHIFT_ENDPOINT']
    user = os.environ['REDSHIFT_USER']
    password = os.environ['REDSHIFT_PASSWORD']
    script_path = os.environ['SQL_SCRIPT_PATH']

    # Download SQL script from S3
    s3 = boto3.client('s3')
    bucket, key = script_path.replace("s3://", "").split("/", 1)
    obj = s3.get_object(Bucket=bucket, Key=key)
    sql_script = obj['Body'].read().decode('utf-8')

    # Connect to Redshift
    conn = psycopg2.connect(
        dbname="datawarehouse",
        user=user,
        password=password,
        host=endpoint,
        port=5439
    )
    cur = conn.cursor()

    try:
        # Execute SQL script
        cur.execute(sql_script)
        conn.commit()
    except Exception as e:
        print(f"Error executing SQL: {e}")
        raise
    finally:
        cur.close()
        conn.close()

    return {"status": "Success"}
