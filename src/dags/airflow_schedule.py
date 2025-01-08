from airflow import DAG
from airflow.providers.amazon.aws.sensors.s3_key import S3KeySensor
from airflow.operators.dummy import DummyOperator
from datetime import datetime

# Define the DAG
default_args = {
    "owner": "airflow",
    "start_date": datetime(2023, 1, 1),
    "retries": 2,
}
dag = DAG(
    "s3_sensor_pipeline",
    default_args=default_args,
    schedule_interval=None,
    catchup=False,
)

# Define the S3 sensor
s3_sensor = S3KeySensor(
    task_id="check_for_new_file",
    bucket_name="your-s3-bucket-name",
    bucket_key="shipping_data/*",  # Prefix to monitor
    aws_conn_id="aws_default",  # AWS connection ID in Airflow
    timeout=60 * 10,  # Timeout in seconds
    poke_interval=30,  # Check every 30 seconds
    dag=dag,
)

# Dummy task to simulate downstream processing
process_data = DummyOperator(task_id="process_new_data", dag=dag)

# Set dependencies
s3_sensor >> process_data
