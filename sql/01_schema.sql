-- =====================================================================
-- 01_schema.sql  |  Tables for the Customer Segmentation project
-- Dialect: SQLite (runs as-is). Notes for PostgreSQL / SQL Server /
-- MySQL are in the comments next to the few dialect-specific lines.
-- =====================================================================

DROP TABLE IF EXISTS transactions;
DROP TABLE IF EXISTS customers;

CREATE TABLE customers (
    customer_id          VARCHAR(10) PRIMARY KEY,
    signup_date          DATE        NOT NULL,
    city                 VARCHAR(50),
    age                  INT,
    gender               VARCHAR(10),
    acquisition_channel  VARCHAR(30)
);

CREATE TABLE transactions (
    transaction_id    VARCHAR(12) PRIMARY KEY,
    customer_id       VARCHAR(10) NOT NULL REFERENCES customers (customer_id),
    transaction_date  DATE        NOT NULL,
    product_category  VARCHAR(40),
    quantity          INT,
    discount_pct      DECIMAL(4, 2),
    amount            DECIMAL(10, 2) NOT NULL,
    channel           VARCHAR(30)
);

CREATE INDEX idx_txn_customer ON transactions (customer_id);
CREATE INDEX idx_txn_date     ON transactions (transaction_date);

-- Load the CSVs
--   SQLite : .mode csv  /  .import --skip 1 data/raw/customers.csv customers
--   Postgres: \copy customers FROM 'data/raw/customers.csv' CSV HEADER
--   SQL Server: BULK INSERT ... WITH (FORMAT = 'CSV', FIRSTROW = 2)
-- (src/load_to_sqlite.py does this automatically.)
