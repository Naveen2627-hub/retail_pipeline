import psycopg2

def create_table_and_copy_data():
    # Redshift connection details
    conn = psycopg2.connect(
        dbname='datawarehouse',
        user='redshiftadmin',
        password='RedshiftPassword123!',
        host='datawarehouse-cluster.cqpwtq4blp9p.us-west-2.redshift.amazonaws.com',
        port='5439'
    )
    cursor = conn.cursor()
    
    # SQL to create the category_totals table
    create_table_query = """
    CREATE TABLE IF NOT EXISTS category_totals (
        category VARCHAR(255) NOT NULL,
        total_stock BIGINT NOT NULL,
        total_stock_value NUMERIC(18, 2) NOT NULL
    )
    DISTSTYLE KEY
    DISTKEY (category)
    SORTKEY (category);
    """
    cursor.execute(create_table_query)
    print("Table created successfully.")
    
    # S3 bucket path and IAM role for Redshift COPY command
    s3_bucket_path = "s3://glue-resources-bucket-8ad42fe9/output/category_totals/"
    iam_role = "arn:aws:iam::975050193031:role/redshift_execution_role"

    # SQL to load data into category_totals from S3
    copy_command = f"""
    COPY category_totals (category, total_stock, total_stock_value)
    FROM '{s3_bucket_path}'
    IAM_ROLE '{iam_role}'
    FORMAT AS PARQUET;
    """
    cursor.execute(copy_command)
    print("Data loaded successfully from S3 to Redshift.")

    # Commit the transaction and close connections
    conn.commit()
    cursor.close()
    conn.close()

# Call the function
create_table_and_copy_data()
