-- =========================================================
-- Repeatable Migration: Stored procedure - top N customers--
-- =========================================================

CREATE OR REPLACE PROCEDURE {{ env_schema }}.SP_GET_TOP_CUSTOMERS(TOP_N NUMBER)
RETURNS TABLE (CUSTOMER_ID NUMBER, CUSTOMER_NAME STRING, LIFETIME_VALUE NUMBER(12,2))
LANGUAGE SQL
AS
$$
BEGIN
    LET res RESULTSET := (
        SELECT c.CUSTOMER_ID,
               c.FIRST_NAME || ' ' || c.LAST_NAME AS CUSTOMER_NAME,
               COALESCE(SUM(o.TOTAL_AMOUNT), 0)   AS LIFETIME_VALUE
        FROM {{ env_schema }}.CUSTOMER c
        LEFT JOIN {{ env_schema }}.ORDERS o
            ON c.CUSTOMER_ID = o.CUSTOMER_ID
        GROUP BY 1, 2
        ORDER BY LIFETIME_VALUE DESC
        LIMIT :TOP_N
    );
    RETURN TABLE(res);
END;
$$;
