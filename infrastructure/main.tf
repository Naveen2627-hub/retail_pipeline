provider "aws" {
  region = "us-west-2"
}

# Generate unique IDs for bucket names
resource "random_id" "extracted_data_bucket_id" {
  byte_length = 8
}

resource "random_id" "transformed_data_bucket_id" {
  byte_length = 8
}

# --- S3 Buckets ---
resource "aws_s3_bucket" "extracted_data_bucket" {
  bucket = "extracted-data-bucket-${random_id.extracted_data_bucket_id.hex}"
}

resource "aws_s3_bucket" "transformed_data_bucket" {
  bucket = "transformed-data-bucket-${random_id.transformed_data_bucket_id.hex}"
}

resource "aws_s3_bucket" "lambda_code_bucket" {
  bucket = "retail-extract-lambda-code"
}

resource "aws_s3_object" "lambda_code_folder" {
  bucket = aws_s3_bucket.lambda_code_bucket.bucket
  key = "lambda/"
}



# --- IAM Role for Lambda ---
resource "aws_iam_role" "lambda_execution_role" {
  name = "lambda_execution_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_policy" "lambda_policy" {
  name   = "lambda_policy"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["s3:PutObject", "s3:GetObject", "s3:ListBucket"]
        Resource = [
          "${aws_s3_bucket.extracted_data_bucket.arn}/*",
          "${aws_s3_bucket.transformed_data_bucket.arn}/*",
          "${aws_s3_bucket.lambda_code_bucket.arn}/*"
        ]
      },
      {
        Effect   = "Allow"
        Action   = ["rds:Connect"]
        Resource = "*"
      },
      {
        Effect   = "Allow"
        Action   = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"]
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_policy_attach" {
  role       = aws_iam_role.lambda_execution_role.name
  policy_arn = aws_iam_policy.lambda_policy.arn
}


#---- Delete line -----
#filename         = "lambda_function.zip" # Ensure this file exists
  
# --- Lambda Function ---
resource "aws_lambda_function" "rds_to_s3_lambda" {
  function_name    = "rds_to_s3_lambda"
  s3_bucket        = aws_s3_bucket.lambda_code_bucket.bucket
  s3_key           = "lambda/rds_to_s3_lambda.zip"
  role             = aws_iam_role.lambda_execution_role.arn
  handler          = "lambda_function.lambda_handler"
  runtime          = "python3.9"
  timeout          = 60

  environment {
    variables = {
      RDS_HOST     = "pos-orders-db.c7goquwgwt1v.us-west-2.rds.amazonaws.com"
      RDS_PORT     = "5432"
      RDS_DB       = "pos_orders_db"
      RDS_USER     = "dbadmin"
      RDS_PASSWORD = "password123"
      S3_BUCKET    = aws_s3_bucket.extracted_data_bucket.bucket
    }
  }
}


/*
# --- RDS Instance ---
resource "aws_vpc" "main_vpc" {
  cidr_block = "10.0.0.0/16"
}

resource "aws_subnet" "private_subnet_1" {
  vpc_id            = aws_vpc.main_vpc.id
  cidr_block        = "10.0.1.0/24"
  availability_zone = "us-west-2a"
}

resource "aws_subnet" "private_subnet_2" {
  vpc_id            = aws_vpc.main_vpc.id
  cidr_block        = "10.0.2.0/24"
  availability_zone = "us-west-2b"
}

resource "aws_db_subnet_group" "default" {
  name        = "default-subnet-group"
  description = "Default RDS subnet group"
  subnet_ids  = [aws_subnet.private_subnet_1.id, aws_subnet.private_subnet_2.id]
}

resource "aws_db_instance" "rds_instance" {
  allocated_storage   = 20
  storage_type        = "gp2"
  engine              = "postgres"
  engine_version      = "13.4"
  instance_class      = "db.t3.micro"
  name                = "pos_orders_db"
  username            = "dbadmin"
  password            = "password123"
  publicly_accessible = true
  skip_final_snapshot = true
  db_subnet_group_name = aws_db_subnet_group.default.name
}
*/
# --- Redshift Cluster ---
resource "aws_iam_role" "redshift_execution_role" {
  name = "redshift_execution_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "redshift.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_policy" "redshift_s3_access_policy" {
  name   = "redshift_s3_access_policy"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["s3:GetObject", "s3:ListBucket"]
        Resource = [
          "${aws_s3_bucket.extracted_data_bucket.arn}/*",
          "${aws_s3_bucket.transformed_data_bucket.arn}/*"
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "redshift_s3_policy_attachment" {
  role       = aws_iam_role.redshift_execution_role.name
  policy_arn = aws_iam_policy.redshift_s3_access_policy.arn
}

resource "aws_redshift_cluster" "redshift_cluster" {
  cluster_identifier      = "datawarehouse-cluster"
  database_name           = "datawarehouse"
  master_username         = "redshiftadmin"
  master_password         = "RedshiftPassword123!"
  node_type               = "dc2.large"
  number_of_nodes         = 2
  publicly_accessible     = true
  skip_final_snapshot     = true
  iam_roles               = [aws_iam_role.redshift_execution_role.arn]
}
