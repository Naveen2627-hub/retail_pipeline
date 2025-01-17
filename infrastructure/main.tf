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

resource "random_id" "glue_bucket_id" {
  byte_length = 4
}

# ---------------S3 Bucket for Glue script and dependencies -------------

resource "aws_s3_bucket" "glue_resources" {
  bucket = "glue-resources-bucket-${random_id.glue_bucket_id.hex}"
}

resource "aws_s3_object" "glue_script" {
  bucket = aws_s3_bucket.glue_resources.bucket
  key    = "scripts/"
}

resource "aws_s3_object" "glue_dependencies" {
  bucket = aws_s3_bucket.glue_resources.bucket
  key    = "dependencies/"
}

resource "aws_s3_bucket" "sql_scripts" {
  bucket = "redshift-sql-scripts-${random_id.glue_bucket_id.hex}"
}

resource "aws_s3_object" "sql_script" {
  bucket = aws_s3_bucket.sql_scripts.bucket
  key    = "scripts/redshift_setup.sql"
  source = "redshift_setup.sql"
}

# ------------------ IAM Role for Lambda ---

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



# ------------- Glue Job ---------------------

resource "aws_glue_job" "glue_job" {
  name     = "glue-transform-job"
  role_arn = aws_iam_role.glue_role.arn

  command {
    name            = "glueetl"
    script_location = "s3://${aws_s3_bucket.glue_resources.bucket}/scripts/glue_transform.py"
    python_version  = "3"
  }

  max_capacity = 5

  default_arguments = {
    "--input_inventory"      = "s3://extracted-data-bucket-7d1207477e5d4493/Inventory/inventory_data.csv"
    "--input_products"       = "s3://extracted-data-bucket-7d1207477e5d4493/rds_data/products.csv"
    "--output_path"          = "s3://${aws_s3_bucket.glue_resources.bucket}/output/"
    "--extra-py-files"       = "s3://${aws_s3_bucket.glue_resources.bucket}/dependencies/"
    "--enable-glue-datacatalog" = "true"
  }

  glue_version = "3.0" 
}

# IAM Role for Glue
resource "aws_iam_role" "glue_role" {
  name = "glue_service_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Principal = {
          Service = "glue.amazonaws.com"
        },
        Action = "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "glue_redshift_access" {
  role       = aws_iam_role.glue_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonRedshiftAllCommandsFullAccess"
}

resource "aws_iam_role_policy_attachment" "glue_s3_access" {
  role       = aws_iam_role.glue_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3FullAccess"
}

resource "aws_iam_role_policy_attachment" "glue_service_role" {
  role       = aws_iam_role.glue_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSGlueServiceRole"
}


# ---------------- Redshift Cluster -------------------------------

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



# Lambda Function Role
resource "aws_iam_role" "lambda_role" {
  name = "lambda_redshift_executor"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Action    = "sts:AssumeRole",
        Effect    = "Allow",
        Principal = {
          Service = "lambda.amazonaws.com"        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_policy" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

/*
resource "aws_lambda_function" "redshift_executor" {
  function_name = "execute_redshift_sql"
  role          = aws_iam_role.lambda_role.arn
  runtime       = "python3.9"
  handler       = "lambda_function.lambda_handler"

  # Provide the source code for Lambda function
  filename         = "lambda_function.zip"
  source_code_hash = filebase64sha256("lambda_function.zip")

  environment {
    variables = {
      REDSHIFT_ENDPOINT = "datawarehouse-cluster.cqpwtq4blp9p.us-west-2.redshift.amazonaws.com:5439/datawarehouse"
      REDSHIFT_USER     = "redshiftadmin"
      REDSHIFT_PASSWORD = "RedshiftPassword123!"
      SQL_SCRIPT_PATH   = "s3://${aws_s3_bucket.sql_scripts.bucket}/scripts/redshift_setup.sql"
    }
  }
}

*/