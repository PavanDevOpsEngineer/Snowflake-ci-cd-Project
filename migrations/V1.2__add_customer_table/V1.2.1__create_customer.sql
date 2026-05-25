-- =========================================================
--Migration: V1.2.1 - Create CUSTOMER table
-- =========================================================

CREATE TABLE IF NOT EXISTS {{ env_schema }}.CUSTOMER (
    CUSTOMER_ID   NUMBER AUTOINCREMENT PRIMARY KEY,
    FIRST_NAME    STRING NOT NULL,
    LAST_NAME     STRING NOT NULL,
    EMAIL         STRING UNIQUE NOT NULL,
    PHONE         STRING,
    COUNTRY       STRING,
    CREATED_AT    TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    UPDATED_AT    TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
)
COMMENT = 'Master customer table';

CREATE INDEX IF NOT EXISTS IDX_CUSTOMER_EMAIL ON {{ env_schema }}.CUSTOMER(EMAIL);
--