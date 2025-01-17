import sys
import pandas as pd
from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, sum

# Initialize Glue context
args = getResolvedOptions(sys.argv, ["JOB_NAME", "input_inventory", "input_products", "output_path"])
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args["JOB_NAME"], args)

print("connection Success!!!!!")

# Read Inventory CSV into Pandas
inventory_df = pd.read_csv(args["input_inventory"])
products_df = pd.read_csv(args["input_products"])

#Comment to trigger workflow
# Inspect and convert data types in Inventory
inventory_df["stock"] = pd.to_numeric(inventory_df["stock"], errors="coerce")

# Inspect and convert data types in Products
products_df["price"] = pd.to_numeric(products_df["price"], errors="coerce")

# Merge the two dataframes
merged_df = pd.merge(inventory_df, products_df, on="product_id", how="inner")

# Calculate total value for each product
merged_df["total_value"] = merged_df["stock"] * merged_df["price"]

# Convert Pandas DataFrame back to Spark DataFrame
merged_spark_df = spark.createDataFrame(merged_df)

# Save product totals to S3
product_totals_output_path = args["output_path"] + "product_totals/"
merged_spark_df.write.format("parquet").mode("overwrite").save(product_totals_output_path)

# Aggregate data to calculate category totals
category_totals_df = (
    merged_spark_df.groupBy("category")
    .agg(
        sum("stock").alias("total_stock"),
        sum("total_value").alias("total_category_value"),
    )
)

# Save category totals to S3
category_totals_output_path = args["output_path"] + "category_totals/"
category_totals_df.write.format("parquet").mode("overwrite").save(category_totals_output_path)

# Commit job
job.commit()
