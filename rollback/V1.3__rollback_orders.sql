-- Rollback for V1.3.1 - drop ORDERS table
DROP TABLE IF EXISTS {{ env_schema }}.ORDERS;
