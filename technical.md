# Technical Documentation

## System Architecture

### Infrastructure Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        GitHub Repository                         │
├─────────────────────────────────────────────────────────────────┤
│  .github/workflows/    migrations/    scripts/    tests/         │
└──────────┬──────────────────┬──────────────┬────────────────────┘
           │                  │              │
           ▼                  ▼              ▼
┌──────────────────┐  ┌─────────────┐  ┌──────────────┐
│  GitHub Actions  │  │ schemachange│  │    pytest     │
│  (Orchestrator)  │──│  (Deployer) │──│  (Validator)  │
└────────┬─────────┘  └──────┬──────┘  └──────┬───────┘
         │                   │                 │
         ▼                   ▼                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Snowflake Cloud                              │
├─────────────┬─────────────────┬─────────────────────────────────┤
│   DEV_DB    │      QA_DB      │           PROD_DB               │
│   ├─ APP    │      ├─ APP     │           ├─ APP                │
│   └─ SCHEMA │      └─ SCHEMA  │           └─ SCHEMACHANGE       │
│     CHANGE  │        CHANGE   │              └─ CHANGE_HISTORY  │
└─────────────┴─────────────────┴─────────────────────────────────┘
```

### Authentication Flow

```
GitHub Secrets (encrypted at rest)
    │
    ▼
GitHub Actions Runner (ephemeral)
    │
    ├── SNOWFLAKE_PASSWORD env var → schemachange
    └── SF_PASSWORD env var → pytest / scripts
    │
    ▼
Snowflake (CICD_ROLE via GITHUB_CICD_USER)
```

## Component Details

### schemachange (v3.7.0)

**Purpose**: Database migration engine that tracks and applies SQL changes.

**How it works**:
1. Reads `schemachange-config.yml` for connection and configuration
2. Scans `migrations/` folder for SQL files
3. Compares against `SCHEMACHANGE.CHANGE_HISTORY` table
4. Applies new/changed scripts in order
5. Records execution in change history

**Configuration** (`schemachange-config.yml`):
- `config-version: 2` — Required for schemachange 3.7+
- `autocommit: false` — Ensures atomic deployments
- `snowflake-schema: SCHEMACHANGE` — Where change history lives
- `query-tag: schemachange-cicd` — Enables audit trail in Snowflake query history
- `vars.env_schema` — Jinja variable available in all migration scripts

**Environment variable resolution**:
- schemachange uses `SNOWFLAKE_PASSWORD` (not `SF_PASSWORD`)
- All other params use Jinja `{{ env_var("NAME") }}` syntax in config
- Variables in `vars:` block are available in SQL as `{{ var_name }}`

### GitHub Actions Workflows

#### ci-validate.yml — PR Gate
```
Trigger: Pull request to develop or main
Purpose: Prevent bad SQL from being merged
Steps:
  1. sqlfluff lint (fails PR if violations found)
  2. schemachange dry-run (validates scripts parse correctly)
```

**Design decisions**:
- No `|| true` on lint — lint failures MUST block the PR
- Uses DEV database for dry-run (least privilege, no prod access needed)
- Triggers on workflow file changes too (catches CI breakage)

#### cd-dev.yml — DEV Deployment
```
Trigger: Push to develop branch (path-filtered)
Purpose: Fast feedback loop for developers
Steps:
  1. Dry-run (catch issues before apply)
  2. Deploy migrations
  3. Run all post-deploy tests
```

**Design decisions**:
- `cancel-in-progress: false` — Never cancel a running deployment
- Pip caching for faster runs
- All test markers run (smoke + qa + load) for full validation

#### cd-qa.yml — QA Deployment
```
Trigger: workflow_run (after DEV succeeds)
Purpose: Promote validated changes to QA
Steps:
  1. Checkout exact commit that passed DEV
  2. Dry-run
  3. Deploy migrations
  4. Run QA + load tests
```

**Design decisions**:
- `ref: github.event.workflow_run.head_sha` — Ensures same code that passed DEV
- Only triggers if DEV conclusion is `success`
- Separate environment for optional approval rules

#### cd-prod.yml — PROD Deployment
```
Trigger: Push to main OR manual workflow_dispatch
Purpose: Safe production deployment with rollback capability
Steps:
  1. DDL backup (disaster recovery)
  2. Dry-run
  3. Deploy OR rollback
  4. Smoke tests
  5. Slack notification on failure
```

**Design decisions**:
- `environment: prod` — Requires manual approval in GitHub UI
- `workflow_dispatch` with choice input — Supports deploy AND rollback
- Pre-deploy backup ensures recovery is always possible
- Smoke tests run even after rollback (validates consistency)

### Rollback System

#### Architecture
```
cd-prod.yml (action=rollback)
    │
    ▼
scripts/rollback.py
    │
    ├── Find matching SQL files in rollback/
    ├── BEGIN transaction
    ├── Execute rollback scripts (reverse order)
    ├── DELETE from CHANGE_HISTORY (versions > target)
    ├── COMMIT (or ROLLBACK on error)
    └── Close connection
```

#### Transaction Safety
- All rollback SQL executes within a single transaction
- If any statement fails, the entire transaction is rolled back
- CHANGE_HISTORY is cleaned up so schemachange can re-deploy corrected versions
- Connection is always closed via `finally` block

#### File Naming Convention
```
rollback/
├── V1.1__undo_initial_setup.sql
├── V1.2__undo_customer_changes.sql
└── V1.3__undo_orders_changes.sql
```

### Backup System (scripts/backup_ddl.py)

**Purpose**: Capture current state of all objects before deployment.

**Process**:
1. Connect to target database
2. Enumerate all schemas (excluding INFORMATION_SCHEMA)
3. For each schema: capture DDL for all tables and views via `GET_DDL()`
4. Save as timestamped JSON file in `backups/` directory

**Output format**:
```json
{
  "database": "PROD_DB",
  "timestamp": "2026-05-25T10:30:00",
  "schemas": {
    "APP": {
      "tables": [{"name": "CUSTOMERS", "ddl": "CREATE TABLE..."}],
      "views": [{"name": "V_ACTIVE_CUSTOMERS", "ddl": "CREATE VIEW..."}]
    }
  }
}
```

### Testing Framework

**Markers**:
| Marker | When it runs | Purpose |
|--------|-------------|---------|
| `smoke` | All environments (DEV, QA, PROD) | Quick object existence checks |
| `qa` | QA only | Data integrity, CRUD operations |
| `load` | QA only | Bulk insert performance |

**Fixture design**:
- `sf_connection` (session-scoped) — One connection per test session
- `cursor` (function-scoped) — Fresh cursor per test
- Tests clean up after themselves (DELETE inserted rows)

## Security Considerations

### Credentials
- All credentials stored in GitHub encrypted secrets
- `GITHUB_CICD_USER` is a service account (not personal)
- `CICD_ROLE` has least-privilege grants (only what's needed)
- No credentials in source code or config files

### Network
- GitHub Actions runners connect to Snowflake via public internet
- Consider: IP allowlisting, private connectivity, or key-pair auth for production

### Recommended Production Hardening
1. Replace password auth with key-pair authentication
2. Add IP allowlist for GitHub Actions runner IPs
3. Use separate service accounts per environment
4. Enable MFA on the Snowflake account
5. Rotate credentials on a schedule
6. Audit via `query-tag` in Snowflake query history

## Monitoring & Observability

### Query History
All schemachange deployments are tagged with `schemachange-cicd`:
```sql
SELECT *
FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
WHERE QUERY_TAG = 'schemachange-cicd'
ORDER BY START_TIME DESC;
```

### Change History
Track what was deployed and when:
```sql
SELECT * FROM DEV_DB.SCHEMACHANGE.CHANGE_HISTORY ORDER BY INSTALLED_ON DESC;
```

### GitHub Actions
- Check workflow run history in **Actions** tab
- Failed deployments trigger Slack notifications (QA + PROD)
- Each run is linked in Slack messages for quick debugging

## Troubleshooting

### Common Issues

| Symptom | Root Cause | Resolution |
|---------|-----------|------------|
| `Authentication failed` | Wrong `SNOWFLAKE_PASSWORD` env var | Ensure deploy steps use `SNOWFLAKE_PASSWORD`, not `SF_PASSWORD` |
| `Change already applied` | Version exists in CHANGE_HISTORY | Create a new version number |
| `Object already exists` | Non-idempotent migration | Use `CREATE OR REPLACE` or `IF NOT EXISTS` |
| `QA deployed wrong code` | Missing `ref` in checkout | Use `ref: github.event.workflow_run.head_sha` |
| `Rollback partially applied` | No transaction wrapping | Ensure BEGIN/COMMIT/ROLLBACK in rollback.py |
| `Dry-run passes, deploy fails` | Permission issues | Verify CICD_ROLE grants on target database |
| `Tests can't connect` | Missing env vars in test step | Check all SF_* vars are set in test step env |

### Debug Commands

```bash
# Check what schemachange would deploy (without applying)
schemachange deploy --config-folder . --dry-run --verbose

# Check change history
snow sql -q "SELECT * FROM DEV_DB.SCHEMACHANGE.CHANGE_HISTORY ORDER BY INSTALLED_ON DESC"

# Verify role grants
snow sql -q "SHOW GRANTS TO ROLE CICD_ROLE"

# Check query tag audit trail
snow sql -q "SELECT QUERY_TEXT, START_TIME, EXECUTION_STATUS FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY WHERE QUERY_TAG = 'schemachange-cicd' ORDER BY START_TIME DESC LIMIT 20"
```

## Performance Considerations

- `CICD_WH` is X-Small with auto-suspend at 60 seconds — cost-efficient for deployments
- `autocommit: false` batches statements within a migration — fewer round trips
- Pip caching in GitHub Actions reduces install time by ~30 seconds
- `cancel-in-progress: false` prevents concurrent deploy corruption

## Future Enhancements

1. **Key-pair authentication** — Eliminate password rotation burden
2. **Terraform for infrastructure** — Manage warehouses, roles, databases as code
3. **Blue-green deployments** — Zero-downtime schema changes
4. **Automated rollback on test failure** — Auto-trigger rollback if smoke tests fail
5. **Multi-region** — Deploy to secondary Snowflake accounts for DR
6. **Schema drift detection** — Alert if manual changes bypass CI/CD
