#!/bin/bash

set -e

# Install dependencies and package the Lambda function
mkdir -p package
pip install -r requirements.txt -t package/
cp src/data_extraction/lambda_function.py package/
cd package
zip -r ../rds_to_s3_lambda.zip .
cd ..

# Upload to S3
aws s3 cp rds_to_s3_lambda.zip s3://retail-extract-lambda-code/lambda/rds_to_s3_lambda.zip
