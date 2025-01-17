-- Create schema
CREATE SCHEMA IF NOT EXISTS public;

-- Create product_totals table
CREATE TABLE IF NOT EXISTS public.product_totals (
    product_id VARCHAR(255),
    product_name VARCHAR(255),
    category VARCHAR(255),
    stock INT,
    price FLOAT8,
    total_value FLOAT8
);

-- Create category_totals table
CREATE TABLE IF NOT EXISTS public.category_totals (
    category VARCHAR(255),
    total_stock INT,
    total_category_value FLOAT8
);
