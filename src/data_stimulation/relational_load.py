import boto3
import psycopg2
import random
from faker import Faker
from decimal import Decimal

# Initialize Faker
fake = Faker()

# AWS Configuration
aws_region = "us-west-2"

# DynamoDB for Inventory
def create_dynamodb_inventory_table():
    dynamodb = boto3.client('dynamodb', region_name=aws_region)
    table_name = "Inventory"

    try:
        response = dynamodb.describe_table(TableName=table_name)
        print(f"DynamoDB Table '{table_name}' already exists.")
    except dynamodb.exceptions.ResourceNotFoundException:
        try:
            dynamodb_resource = boto3.resource('dynamodb', region_name=aws_region)
            table = dynamodb_resource.create_table(
                TableName=table_name,
                KeySchema=[
                    {'AttributeName': 'product_id', 'KeyType': 'HASH'}
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'product_id', 'AttributeType': 'S'}
                ],
                ProvisionedThroughput={
                    'ReadCapacityUnits': 5,
                    'WriteCapacityUnits': 5
                }
            )
            table.wait_until_exists()
            print(f"DynamoDB Table '{table_name}' created successfully.")
        except Exception as e:
            print(f"Error creating DynamoDB Table: {e}")

# Populate DynamoDB Inventory Table
def populate_dynamodb_inventory():
    dynamodb = boto3.resource('dynamodb', region_name=aws_region)
    table = dynamodb.Table("Inventory")

    for _ in range(50):
        item = {
            "product_id": fake.uuid4(),
            "product_name": fake.word(),
            "stock": random.randint(10, 500),
            "price": Decimal(str(round(random.uniform(5, 500), 2)))  # Use Decimal for price
        }
        table.put_item(Item=item)
    print("DynamoDB Inventory table populated with dummy data.")

# S3 Bucket for Webserver Logs
def create_s3_bucket():
    s3 = boto3.client('s3', region_name=aws_region)
    bucket_name = "webserver-logs-sample"

    try:
        response = s3.head_bucket(Bucket=bucket_name)
        print(f"S3 Bucket '{bucket_name}' already exists.")
    except s3.exceptions.ClientError:
        try:
            s3.create_bucket(
                Bucket=bucket_name,
                CreateBucketConfiguration={'LocationConstraint': aws_region}
            )
            print(f"S3 Bucket '{bucket_name}' created successfully.")
        except Exception as e:
            print(f"Error creating S3 Bucket: {e}")

# Upload Dummy Logs to S3
def upload_dummy_logs_to_s3():
    s3 = boto3.client('s3', region_name=aws_region)
    bucket_name = "webserver-logs-sample"

    for i in range(10):
        log_data = {
            "session_id": fake.uuid4(),
            "user_id": fake.uuid4(),
            "timestamp": fake.date_time_this_year().isoformat(),
            "action": fake.word(),
        }
        s3.put_object(
            Bucket=bucket_name,
            Key=f"logs/log_{i+1}.json",
            Body=str(log_data)
        )
    print("Dummy webserver logs uploaded to S3.")

# RDS for POS and Orders
def create_rds_instance():
    rds = boto3.client('rds', region_name=aws_region)
    db_instance_identifier = "pos-orders-db"

    try:
        response = rds.describe_db_instances(DBInstanceIdentifier=db_instance_identifier)
        print(f"RDS Instance '{db_instance_identifier}' already exists.")
    except rds.exceptions.DBInstanceNotFoundFault:
        try:
            response = rds.create_db_instance(
                DBName='pos_orders_db',
                DBInstanceIdentifier=db_instance_identifier,
                AllocatedStorage=20,
                DBInstanceClass='db.t3.micro',  # Update to a supported instance class
                Engine='postgres',
                MasterUsername='dbadmin',
                MasterUserPassword='password123',
            )
            print(f"RDS Instance '{db_instance_identifier}' is being created. This can take a few minutes.")
        except Exception as e:
            print(f"Error creating RDS instance: {e}")

# Create Tables in RDS and Populate Data
def create_rds_tables_and_populate():
    connection = psycopg2.connect(
        host="pos-orders-db.c7goquwgwt1v.us-west-2.rds.amazonaws.com",  # Replace with your RDS endpoint
        database="pos_orders_db",
        user="dbadmin",       # Use the correct username
        password="password123"
    )
    cursor = connection.cursor()

    # Create Customers Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            customer_id UUID PRIMARY KEY,
            name VARCHAR(255),
            email VARCHAR(255),
            phone VARCHAR(50)
        );
    """)

    # Create Products Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            product_id UUID PRIMARY KEY,
            name VARCHAR(255),
            price DECIMAL(10, 2),
            category VARCHAR(255)
        );
    """)

    # Create Transactions Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            transaction_id UUID PRIMARY KEY,
            customer_id UUID,
            product_id UUID,
            quantity INT,
            total_price DECIMAL(10, 2),
            FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
            FOREIGN KEY (product_id) REFERENCES products(product_id)
        );
    """)

    # Populate Customers
    print("Populating Customers table...")
    cursor.execute("DELETE FROM customers;")  # Clear old data for idempotency
    for _ in range(100):
        cursor.execute("""
            INSERT INTO customers (customer_id, name, email, phone)
            VALUES (%s, %s, %s, %s)
        """, (
            fake.uuid4(),
            fake.name(),
            fake.email(),
            fake.phone_number(),
        ))

    # Populate Products
    print("Populating Products table...")
    cursor.execute("DELETE FROM products;")  # Clear old data for idempotency
    for _ in range(50):
        cursor.execute("""
            INSERT INTO products (product_id, name, price, category)
            VALUES (%s, %s, %s, %s)
        """, (
            fake.uuid4(),
            fake.word(),
            Decimal(str(round(random.uniform(10, 100), 2))),
            fake.word(),
        ))

    # Fetch Valid IDs
    cursor.execute("SELECT customer_id FROM customers;")
    customer_ids = [row[0] for row in cursor.fetchall()]

    cursor.execute("SELECT product_id FROM products;")
    product_ids = [row[0] for row in cursor.fetchall()]

    # Populate Transactions
    print("Populating Transactions table...")
    cursor.execute("DELETE FROM transactions;")  # Clear old data for idempotency
    for _ in range(200):
        cursor.execute("""
            INSERT INTO transactions (transaction_id, customer_id, product_id, quantity, total_price)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            fake.uuid4(),
            random.choice(customer_ids),  # Use valid customer_id
            random.choice(product_ids),  # Use valid product_id
            random.randint(1, 5),
            Decimal(str(round(random.uniform(10, 500), 2))),
        ))

    connection.commit()
    cursor.close()
    connection.close()
    print("RDS tables created and populated with dummy data.")


# Main Function
if __name__ == "__main__":
    print("Starting data source setup...")
    create_dynamodb_inventory_table()
    populate_dynamodb_inventory()
    create_s3_bucket()
    upload_dummy_logs_to_s3()
    create_rds_instance()
    print("Waiting for RDS instance to be ready... (Run 'create_rds_tables_and_populate' after RDS setup completes.)")
    create_rds_tables_and_populate()
    
