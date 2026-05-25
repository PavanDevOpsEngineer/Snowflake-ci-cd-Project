-- =========================================================
-- Repeatable Migration: Customer-Orders denormalized view
-- Re-runs automatically whenever the file hash changes.---
-- =========================================================

CREATE OR REPLACE VIEW {{ env_schema }}.VW_CUSTOMER_ORDERS AS
SELECT
    c.CUSTOMER_ID,
    c.FIRST_NAME || ' ' || c.LAST_NAME AS CUSTOMER_NAME,
    c.EMAIL,
    c.COUNTRY,
    o.ORDER_ID,
    o.ORDER_DATE,
    o.TOTAL_AMOUNT,
    o.STATUS
FROM {{ env_schema }}.CUSTOMER c
LEFT JOIN {{ env_schema }}.ORDERS o
    ON c.CUSTOMER_ID = o.CUSTOMER_ID;
