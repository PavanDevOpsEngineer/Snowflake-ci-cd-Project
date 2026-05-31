"""Execute rollback scripts from /rollback for a given target version.

Usage (via GH Actions): TARGET_VERSION=V1.3 python scripts/rollback.py
"""
import os
import glob
import sys
import snowflake.connector


def main():
    def get_env(name, required=True):
        val = os.environ.get(name)
        if val is None:
            if required:
                sys.exit(f"{name} env var is required")
            return None
        v = val.strip()
        if v in ("", '""', "''"):
            if required:
                sys.exit(f"{name} env var is empty or invalid: {val!r}")
            return None
        if len(v) >= 2 and v[0] == v[-1] and v[0] in ("'", '"'):
            v = v[1:-1].strip()
        if v == "":
            if required:
                sys.exit(f"{name} env var is empty after stripping quotes")
            return None
        return v

    target = get_env("TARGET_VERSION")

    pattern = f"rollback/{target}*.sql"
    files = sorted(glob.glob(pattern), reverse=True)
    if not files:
        sys.exit(f"No rollback scripts found matching {pattern}")

    account = get_env("SF_ACCOUNT")
    user = get_env("SF_USER")
    password = get_env("SF_PASSWORD")
    role = get_env("SF_ROLE", required=False)
    warehouse = get_env("SF_WAREHOUSE", required=False)
    database = get_env("SF_DATABASE")
    schema = os.environ.get("SF_SCHEMA", "APP")

    conn = snowflake.connector.connect(
        account=account,
        user=user,
        password=password,
        role=role,
        warehouse=warehouse,
    )

    try:
        cur = conn.cursor()
        if database:
            cur.execute(f"USE DATABASE {database}")
        cur.execute("BEGIN")

        for f in files:
            print(f"Executing rollback: {f}")
            with open(f) as fh:
                sql = fh.read().replace("{{ env_schema }}", schema)
            for stmt in [s.strip() for s in sql.split(";") if s.strip()]:
                cur.execute(stmt)

        cur.execute(f"""
            DELETE FROM {database}.SCHEMACHANGE.CHANGE_HISTORY
            WHERE VERSION > '{target}'
        """)
        cur.execute("COMMIT")
        print("Rollback completed successfully.")
    except Exception as e:
        try:
            # attempt to rollback if cursor/connection available; ignore any errors here
            cur.execute("ROLLBACK")
        except Exception:
            pass
        raise RuntimeError(f"Rollback failed, transaction rolled back: {e}")
    finally:
        conn.close()


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
