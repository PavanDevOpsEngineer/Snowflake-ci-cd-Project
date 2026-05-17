-- =========================================================
--Migration: V1.3.1 - Create ORDERS table with FK
-- =========================================================

CREATE TABLE IF NOT EXISTS {{ env_schema }}.ORDERS (
    ORDER_ID      NUMBER AUTOINCREMENT PRIMARY KEY,
    CUSTOMER_ID   NUMBER NOT NULL,
    ORDER_DATE    DATE NOT NULL,
    TOTAL_AMOUNT  NUMBER(12,2) NOT NULL,
    STATUS        STRING DEFAULT 'PENDING',
    CREATED_AT    TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    CONSTRAINT FK_ORDERS_CUSTOMER FOREIGN KEY (CUSTOMER_ID)
        REFERENCES {{ env_schema }}.CUSTOMER(CUSTOMER_ID)
)
COMMENT = 'Customer orders fact table';
