#Provider
provider "aws" {
    region = "us-west-2"
}

#S3 Bucket to maintain dump of all the Shipping address data 
resource "aws_s3_bucket" "shipping_bucket" {
    bucket = "retail-shipping-address-dump-01082025"
    tags = {
        Name = "ShippingDataBucket"
        Environment = "Dev"
        Project = "Retail"
    }
}

#Adding a bucket policy to allow access
resource "aws_s3_bucket_policy" "shipping_bucket_policy" {
  bucket = aws_s3_bucket.shipping_bucket.id

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Sid       = "AllowSpecificIAMAccess",
        Effect    = "Allow",
        Principal = {
          AWS = "arn:aws:iam::975050193031:user/dataengineering"  # Replace with the appropriate user/role ARN
        },
        Action    = [
          "s3:PutObject",
          "s3:GetObject",
          "s3:ListBucket"
        ],
        Resource  = [
          aws_s3_bucket.shipping_bucket.arn,
          "${aws_s3_bucket.shipping_bucket.arn}/*"
        ]
      }
    ]
  })
}

#Create an IAM Role for Airflow to access S3 
resource "aws_iam_role" "airflow_s3_role" {
    name = "airflow_s3_role"

    assume_role_policy = jsonencode({
        Version = "2012-10-17",
        Statement = [
            {
                Effect = "Allow"
                Principal = {
                    Service = "ecs-tasks.amazonaws.com"  #if running airflow on EC2
                }
                Action = "sts:AssumeRole"
            }
        ]
    })
}


# Attaching S3 read/write permission to IAM Role
resource "aws_iam_role_policy" "airflow_s3_policy" {
    name = "airflow_s3_policy"
    role = aws_iam_role.airflow_s3_role.id
    policy = jsonencode({
        Version = "2012-10-17",
        Statement = [
            {
                Effect = "Allow"
                Action = [
                    "s3:PutObject",
                    "s3:GetObject",
                    "s3:ListBucket"
                ]
                Resource = [
                    aws_s3_bucket.shipping_bucket.arn,
                    "${aws_s3_bucket.shipping_bucket.arn}/*"
                ]
            }
        ]
    })
}


# Output the bucket name
output "s3_bucket_name" {
  value = aws_s3_bucket.shipping_bucket.bucket
}

# Output the IAM role ARN for Airflow
output "airflow_role_arn" {
  value = aws_iam_role.airflow_s3_role.arn
}