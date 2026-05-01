"""Schema validation & regression tests for Snowflake deployments."""
import pytest


EXPECTED_TABLES = {"AUDIT_LOG", "CUSTOMER", "ORDERS"}
EXPECTED_VIEWS = {"VW_CUSTOMER_ORDERS"}


def test_tables_exist(cur):
    cur.execute("SHOW TABLES IN SCHEMA APP")
    tables = {r[1].upper() for r in cur.fetchall()}
    missing = EXPECTED_TABLES - tables
    assert not missing, f"Missing tables: {missing}"


def test_views_exist(cur):
    cur.execute("SHOW VIEWS IN SCHEMA APP")
    views = {r[1].upper() for r in cur.fetchall()}
    assert EXPECTED_VIEWS.issubset(views)


def test_customer_columns(cur):
    cur.execute("DESC TABLE APP.CUSTOMER")
    cols = {r[0].upper() for r in cur.fetchall()}
    required = {"CUSTOMER_ID", "FIRST_NAME", "LAST_NAME", "EMAIL", "CREATED_AT"}
    assert required.issubset(cols)


def test_orders_fk_to_customer(cur):
    cur.execute(
        """SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS
           WHERE TABLE_NAME = 'ORDERS' AND CONSTRAINT_TYPE = 'FOREIGN KEY'"""
    )
    assert cur.fetchone()[0] >= 1


@pytest.mark.smoke
def test_change_history_populated(cur):
    cur.execute("SELECT COUNT(*) FROM SCHEMACHANGE.CHANGE_HISTORY")
    assert cur.fetchone()[0] > 0


@pytest.mark.qa
def test_view_returns_data_shape(cur):
    cur.execute("SELECT * FROM APP.VW_CUSTOMER_ORDERS LIMIT 1")
    desc = [d[0].upper() for d in cur.description]
    for col in ("CUSTOMER_ID", "CUSTOMER_NAME", "ORDER_ID"):
        assert col in desc


@pytest.mark.load
@pytest.mark.timeout(60)
def test_bulk_insert_performance(cur):
    cur.execute(
        """INSERT INTO APP.CUSTOMER (FIRST_NAME, LAST_NAME, EMAIL)
           SELECT 'T', 'User' || SEQ4(), 'u' || SEQ4() || '@load.test'
           FROM TABLE(GENERATOR(ROWCOUNT => 10000))"""
    )
    cur.execute("SELECT COUNT(*) FROM APP.CUSTOMER WHERE EMAIL LIKE '%@load.test'")
    assert cur.fetchone()[0] >= 10000
    # cleanup
    cur.execute("DELETE FROM APP.CUSTOMER WHERE EMAIL LIKE '%@load.test'")
