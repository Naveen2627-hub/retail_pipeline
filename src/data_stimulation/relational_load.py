from faker import Faker
import pymysql

fake = Faker()
connection = pymysql.connect(host='172.22.128.1', user='root', password='Njoyllu@143', database='retail20250107')
cursor = connection.cursor()

# Insert dummy data for POS sales
for _ in range(10000):
    query = "INSERT INTO pos_sales (customer_id, product_id, store_id, quantity, sale_date, total_amount, discount_amount) VALUES (%s, %s, %s, %s, %s, %s, %s)"
    values = (fake.random_int(1, 100), fake.random_int(1, 50), fake.random_int(1, 10), fake.random_int(1, 5), fake.date_time(), fake.random_int(20, 500), fake.random_int(0, 50))
    cursor.execute(query, values)

connection.commit()
cursor.close()
connection.close()
