"""Export current PROD DDL to a timestamped file for rollback safety."""
import os
import datetime as dt
import snowflake.connector


def main():
    conn = snowflake.connector.connect(
        account=os.environ["SF_ACCOUNT"],
        user=os.environ["SF_USER"],
        password=os.environ["SF_PASSWORD"],
        role=os.environ["SF_ROLE"],
        warehouse=os.environ["SF_WAREHOUSE"],
        database=os.environ["SF_DATABASE"],
    )
    cur = conn.cursor()
    schema = os.environ.get("SF_SCHEMA", "APP")
    cur.execute(f"SHOW TABLES IN SCHEMA {schema}")
    tables = [r[1] for r in cur.fetchall()]

    stamp = dt.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    out = f"backup_ddl_{stamp}.sql"
    with open(out, "w") as f:
        for t in tables:
            cur.execute(f"SELECT GET_DDL('TABLE', '{schema}.{{t}}')")
            f.write(cur.fetchone()[0] + "\n\n")
    print(f"✅ DDL snapshot written to {out}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\u274c Error: {e}")
