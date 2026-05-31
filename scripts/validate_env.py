"""Validate required environment variables for CI runs.

This script is intended to be executed in CI before running schemachange.
It fails fast with a non-zero exit code and a clear message if required
variables are missing or set to empty/quoted-empty values like '""'.
"""
import os
import sys


def is_invalid(val: str) -> bool:
    if val is None:
        return True
    s = val.strip()
    if s in ("", '""', "''"):
        return True
    # unwrap matching surrounding quotes
    if len(s) >= 2 and s[0] == s[-1] and s[0] in ("'", '"'):
        s = s[1:-1].strip()
    return s == ""


def require(name: str):
    val = os.environ.get(name)
    if is_invalid(val):
        print(f"ERROR: environment variable {name} is missing or empty (value: {val!r})", file=sys.stderr)
        sys.exit(2)


def main():
    # required variables for schemachange
    require("SF_ACCOUNT")
    require("SF_USER")
    # schemachange/workflows sometimes use SF_PASSWORD or SNOWFLAKE_PASSWORD
    if is_invalid(os.environ.get("SF_PASSWORD")) and is_invalid(os.environ.get("SNOWFLAKE_PASSWORD")):
        print("ERROR: SF_PASSWORD or SNOWFLAKE_PASSWORD must be set and non-empty", file=sys.stderr)
        sys.exit(2)
    require("SF_DATABASE")

    # optional but recommended
    if is_invalid(os.environ.get("SF_ROLE")):
        print("WARNING: SF_ROLE is not set or empty; proceeding without a role", file=sys.stderr)

    print("Environment validation passed")


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as e:
        print(f"Validation failed: {e}", file=sys.stderr)
        sys.exit(1)
