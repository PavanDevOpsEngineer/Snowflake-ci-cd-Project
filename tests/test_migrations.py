"""Post-deploy validation tests for Snowflake CI/CD."""
import os
import pytest
import snowflake.connector


@pytest.fixture(scope="session")
def sf_connection():
    conn = snowflake.connector.connect(
        account=os.environ["SF_ACCOUNT"],
        user=os.environ["SF_USER"],
        password=os.environ["SF_PASSWORD"],
        role=os.environ["SF_ROLE"],
        warehouse=os.environ["SF_WAREHOUSE"],
    )
    database = os.environ.get("SF_DATABASE", "")
    schema = os.environ.get("SF_SCHEMA", "APP")
    cur = conn.cursor()
    if database:
        cur.execute(f"USE DATABASE {database}")
    if schema:
        cur.execute(f"USE SCHEMA {schema}")
    yield conn
    conn.close()


@pytest.fixture
def cursor(sf_connection):
    return sf_connection.cursor()


@pytest.mark.smoke
def test_customers_table_exists(cursor):
    cursor.execute("SHOW TABLES LIKE 'CUSTOMERS'")
    results = cursor.fetchall()
    assert len(results) == 1, "CUSTOMERS table should exist"


@pytest.mark.smoke
def test_orders_table_exists(cursor):
    cursor.execute("SHOW TABLES LIKE 'ORDERS'")
    results = cursor.fetchall()
    assert len(results) == 1, "ORDERS table should exist"


@pytest.mark.smoke
def test_customers_columns(cursor):
    cursor.execute("DESCRIBE TABLE CUSTOMERS")
    columns = {row[0] for row in cursor.fetchall()}
    expected = {"CUSTOMER_ID", "FIRST_NAME", "LAST_NAME", "EMAIL", "CREATED_AT", "UPDATED_AT"}
    assert expected.issubset(columns), f"Missing columns: {expected - columns}"


@pytest.mark.smoke
def test_orders_columns(cursor):
    cursor.execute("DESCRIBE TABLE ORDERS")
    columns = {row[0] for row in cursor.fetchall()}
    expected = {"ORDER_ID", "CUSTOMER_ID", "ORDER_DATE", "TOTAL_AMOUNT", "STATUS", "CREATED_AT"}
    assert expected.issubset(columns), f"Missing columns: {expected - columns}"


@pytest.mark.qa
def test_insert_and_query_customer(cursor):
    cursor.execute("""
        INSERT INTO CUSTOMERS (FIRST_NAME, LAST_NAME, EMAIL)
        VALUES ('Test', 'User', 'test@cicd.dev')
    """)
    cursor.execute("SELECT COUNT(*) FROM CUSTOMERS WHERE EMAIL = 'test@cicd.dev'")
    count = cursor.fetchone()[0]
    assert count >= 1
    cursor.execute("DELETE FROM CUSTOMERS WHERE EMAIL = 'test@cicd.dev'")


@pytest.mark.qa
def test_foreign_key_constraint(cursor):
    cursor.execute("""
        INSERT INTO CUSTOMERS (FIRST_NAME, LAST_NAME, EMAIL)
        VALUES ('FK', 'Test', 'fk@cicd.dev')
    """)
    cursor.execute("SELECT CUSTOMER_ID FROM CUSTOMERS WHERE EMAIL = 'fk@cicd.dev'")
    cid = cursor.fetchone()[0]
    cursor.execute(f"""
        INSERT INTO ORDERS (CUSTOMER_ID, TOTAL_AMOUNT, STATUS)
        VALUES ({cid}, 99.99, 'COMPLETED')
    """)
    cursor.execute(f"SELECT COUNT(*) FROM ORDERS WHERE CUSTOMER_ID = {cid}")
    assert cursor.fetchone()[0] >= 1
    cursor.execute(f"DELETE FROM ORDERS WHERE CUSTOMER_ID = {cid}")
    cursor.execute("DELETE FROM CUSTOMERS WHERE EMAIL = 'fk@cicd.dev'")


@pytest.mark.load
def test_bulk_insert_performance(cursor):
    values = ", ".join(
        [f"('Load{i}', 'Test{i}', 'load{i}@cicd.dev')" for i in range(100)]
    )
    cursor.execute(f"INSERT INTO CUSTOMERS (FIRST_NAME, LAST_NAME, EMAIL) VALUES {values}")
    cursor.execute("SELECT COUNT(*) FROM CUSTOMERS WHERE EMAIL LIKE '%@cicd.dev'")
    count = cursor.fetchone()[0]
    assert count >= 100
    cursor.execute("DELETE FROM CUSTOMERS WHERE EMAIL LIKE '%load%@cicd.dev'")
