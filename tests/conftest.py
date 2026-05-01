"""Shared pytest fixtures for Snowflake validation."""
import os
import pytest
import snowflake.connector


@pytest.fixture(scope="session")
def sf_conn():
    conn = snowflake.connector.connect(
        account=os.environ["SF_ACCOUNT"],
        user=os.environ["SF_USER"],
        password=os.environ["SF_PASSWORD"],
        role=os.environ["SF_ROLE"],
        warehouse=os.environ["SF_WAREHOUSE"],
        database=os.environ["SF_DATABASE"],
        schema=os.environ.get("SF_SCHEMA", "APP"),
    )
    yield conn
    conn.close()


@pytest.fixture()
def cur(sf_conn):
    c = sf_conn.cursor()
    yield c
    c.close()
