"""Pre-deploy DDL backup script.

Connects to Snowflake and exports current DDL for all objects in the target
database. Saves output as an artifact for disaster recovery.

Usage (via GH Actions): python scripts/backup_ddl.py
"""
import os
import sys
import json
from datetime import datetime
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

    account = get_env("SF_ACCOUNT")
    user = get_env("SF_USER")
    password = get_env("SF_PASSWORD")
    role = get_env("SF_ROLE", required=False)
    warehouse = get_env("SF_WAREHOUSE", required=False)
    database = get_env("SF_DATABASE")

    conn = snowflake.connector.connect(
        account=account,
        user=user,
        password=password,
        role=role,
        warehouse=warehouse,
    )

    cur = conn.cursor()

    try:
        cur.execute(f"USE DATABASE {database}")

        schemas = []
        cur.execute("SHOW SCHEMAS")
        for row in cur.fetchall():
            schema_name = row[1]
            if schema_name not in ("INFORMATION_SCHEMA",):
                schemas.append(schema_name)

        backup = {
            "database": database,
            "timestamp": datetime.utcnow().isoformat(),
            "schemas": {},
        }

        for schema in schemas:
            backup["schemas"][schema] = {"tables": [], "views": []}

            cur.execute(f"SHOW TABLES IN SCHEMA {database}.{schema}")
            for row in cur.fetchall():
                table_name = row[1]
                    cur.execute(f"SELECT GET_DDL('TABLE', '{database}.{schema}.{table_name}')")
                    row = cur.fetchone()
                    ddl = row[0] if row and row[0] is not None else ""
                    backup["schemas"][schema]["tables"].append(
                        {"name": table_name, "ddl": ddl}
                    )

            cur.execute(f"SHOW VIEWS IN SCHEMA {database}.{schema}")
            for row in cur.fetchall():
                view_name = row[1]
                cur.execute(f"SELECT GET_DDL('VIEW', '{database}.{schema}.{view_name}')")
                row = cur.fetchone()
                ddl = row[0] if row and row[0] is not None else ""
                backup["schemas"][schema]["views"].append(
                    {"name": view_name, "ddl": ddl}
                )

        os.makedirs("backups", exist_ok=True)
        filename = f"backups/ddl_backup_{database}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, "w") as f:
            json.dump(backup, f, indent=2)

        print(f"DDL backup saved to {filename}")
        print(f"Schemas backed up: {', '.join(schemas)}")

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
