from pymongo import MongoClient
from faker import Faker
import random

client = MongoClient('mongodb://172.22.128.1:27017/', serverSelectionTimeoutMS=5000)
db = client['macy_db']

fake = Faker()

# Clickstream Data
clickstream = db['clickstream']
clickstream_data = [
    {"session_id": fake.uuid4(), "user_id": random.randint(1, 100), "url": fake.url(), "timestamp": fake.date_time()}
    for _ in range(101)
]
clickstream.insert_many(clickstream_data)

# Customer Data
customers = db['customers']
customer_data = [
    {"customer_id": i, "name": fake.name(), "email": fake.email(), "loyalty_tier": random.choice(["Silver", "Gold", "Platinum"])}
    for i in range(1, 101)
]
customers.insert_many(customer_data)
