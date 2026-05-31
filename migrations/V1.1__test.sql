-- Test: Create a test table
CREATE OR REPLACE TABLE {{ env_schema }}.TEST_TABLE (
    TEST_ID NUMBER AUTOINCREMENT PRIMARY KEY,
    TEST_NAME VARCHAR(100) NOT NULL,
    TEST_VALUE NUMBER(10, 2),
    IS_ACTIVE BOOLEAN DEFAULT TRUE,
    CREATED_AT TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP()
);

-- Verify test table was created
DESCRIBE TABLE {{ env_schema }}.TEST_TABLE;

-- Insert sample data into test table
INSERT INTO {{ env_schema }}.TEST_TABLE (TEST_NAME, TEST_VALUE, IS_ACTIVE)
VALUES
    ('Test A', 10.50, TRUE),
    ('Test B', 20.75, TRUE),
    ('Test C', 30.00, FALSE);

-- Verify data was inserted
SELECT * FROM {{ env_schema }}.TEST_TABLE;
