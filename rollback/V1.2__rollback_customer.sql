-- Rollback for V1.2.1 - drop CUSTOMER table
DROP TABLE IF EXISTS {{ env_schema }}.CUSTOMER;
