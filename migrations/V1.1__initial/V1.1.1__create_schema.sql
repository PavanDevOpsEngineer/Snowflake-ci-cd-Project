-- =========================================================
-- Migration: V1.1.1 - Create base schema & audit objects
-- Author   : CI/CD Bot
--- =========================================================

CREATE SCHEMA IF NOT EXISTS {{ env_schema }}
    COMMENT = 'Application schema managed by schemachange CI/CD';

-- Change tracking is auto-created by schemachange, but we
-- also create an application-level audit table.
CREATE TABLE IF NOT EXISTS {{ env_schema }}.AUDIT_LOG (
    AUDIT_ID      NUMBER AUTOINCREMENT PRIMARY KEY,
    EVENT_TYPE    STRING NOT NULL,
    EVENT_DETAIL  VARIANT,
    CREATED_AT    TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    CREATED_BY    STRING DEFAULT CURRENT_USER()
);
