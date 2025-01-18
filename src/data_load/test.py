import pandas as pd

# Replace with your file's S3 path
parquet_file_path = "s3://glue-resources-bucket-8ad42fe9/output/category_totals/part-00000-a8120898-fa64-4c6a-bdb4-1d78870f56d9-c000.snappy.parquet"
df = pd.read_parquet(parquet_file_path)
print(df.dtypes)