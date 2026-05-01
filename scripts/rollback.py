"""Execute rollback scripts from /rollback for a given target version.

Usage (via GH Actions): TARGET_VERSION=V1.3 python scripts/rollback.py
"""
import os
import glob
import sys
import snowflake.connector


def main():
    target = os.environ.get("TARGET_VERSION", "").strip()
    if not target:
        sys.exit("❌ TARGET_VERSION env var is required (e.g. V1.3)")

    pattern = f"rollback/{target}*.sql"
    files = sorted(glob.glob(pattern), reverse=True)
    if not files:
        sys.exit(f"❌ No rollback scripts found matching {pattern}")

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
    for f in files:
        print(f"⏪ Executing rollback: {f}")
        with open(f) as fh:
            sql = fh.read().replace("{{ env_schema }}", schema)
        for stmt in [s.strip() for s in sql.split(";") if s.strip()]:
            cur.execute(stmt)
    print("✅ Rollback completed.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\u274c Error: {e}")
