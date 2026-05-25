# Snowflake CI/CD Project

Automated database change management for Snowflake using **schemachange** and **GitHub Actions** across dev, qa, and prod environments.

## Architecture

```
feature/* ──► develop ──► (auto-chain) ──► main
    │             │              │             │
 CI Lint     CD DEV          CD QA        CD PROD
 Dry-run     Deploy          Deploy       Deploy
             Tests           QA Tests     Smoke Tests
                                          Approval Gate
                                          DDL Backup
                                          Slack Alerts
```

## Quick Start

### Prerequisites
- Snowflake account with ACCOUNTADMIN access (for initial setup)
- GitHub repository with Actions enabled
- Python 3.11+

### 1. Snowflake Setup

Run `Project-setup.sql` against each environment to create:
- `CICD_ROLE` and `GITHUB_CICD_USER`
- `CICD_WH` warehouse
- `DEV_DB`, `QA_DB`, `PROD_DB` databases
- `SCHEMACHANGE` schema with `CHANGE_HISTORY` table
- Required grants

### 2. GitHub Secrets

Configure these in **Settings → Secrets and variables → Actions**:

| Secret | Value |
|--------|-------|
| `SF_ACCOUNT` | Your Snowflake account identifier |
| `SF_USER` | `GITHUB_CICD_USER` |
| `SF_PASSWORD` | Service account password |
| `SF_ROLE` | `CICD_ROLE` |
| `SF_WAREHOUSE` | `CICD_WH` |
| `SF_DB_DEV` | `DEV_DB` |
| `SF_DB_QA` | `QA_DB` |
| `SF_DB_PROD` | `PROD_DB` |
| `SLACK_WEBHOOK_URL` | Slack incoming webhook URL |

### 3. GitHub Environments

Create environments in **Settings → Environments**:
- `dev` — No protection rules
- `qa` — Optional: require reviewers
- `prod` — Required: manual approval

### 4. Deploy

```bash
git checkout -b feature/my-change
# Add migration to migrations/
git add . && git commit -m "Add migration V1.2"
git push origin feature/my-change
# Create PR → CI validates → Merge → CD deploys
```

## Project Structure

```
├── .github/workflows/
│   ├── ci-validate.yml         # PR gate: lint + dry-run
│   ├── cd-dev.yml              # Auto-deploy to DEV
│   ├── cd-qa.yml               # Auto-deploy to QA (after DEV success)
│   └── cd-prod.yml             # Gated deploy to PROD
├── migrations/
│   └── V1.1__initial_setup.sql # Versioned migrations
├── rollback/                   # Rollback SQL scripts
├── tests/
│   ├── test_migrations.py      # Smoke, QA, load tests
│   ├── requirements.txt        # Test dependencies
│   └── pytest.ini              # Pytest markers
├── scripts/
│   ├── backup_ddl.py           # Pre-deploy DDL backup
│   └── rollback.py             # Transaction-safe rollback
├── schemachange-config.yml     # schemachange configuration
└── Project-setup.sql           # Snowflake account setup
```

## Migration Naming

| Prefix | Behavior | Example |
|--------|----------|---------|
| `V` | Run once (versioned) | `V1.2__add_products.sql` |
| `R` | Re-run on change (repeatable) | `R__create_views.sql` |
| `A` | Run every deploy (always) | `A__refresh_grants.sql` |

## Workflows

| Workflow | Trigger | Environment | Key Steps |
|----------|---------|-------------|-----------|
| `ci-validate.yml` | PR to develop/main | — | sqlfluff lint, dry-run |
| `cd-dev.yml` | Push to develop | dev | Dry-run, deploy, tests |
| `cd-qa.yml` | DEV workflow success | qa | Dry-run, deploy, QA tests |
| `cd-prod.yml` | Push to main / manual | prod | Backup, dry-run, deploy, smoke tests |

## Rollback

### Automatic (via GitHub Actions)
1. Go to **Actions → CD - Deploy to PROD**
2. Click **Run workflow**
3. Select `rollback` and enter target version (e.g., `V1.1`)

### Manual
```bash
export SF_ACCOUNT=... SF_USER=... SF_PASSWORD=... SF_ROLE=... SF_WAREHOUSE=... SF_DATABASE=...
export TARGET_VERSION=V1.1
python scripts/rollback.py
```

## Testing

Tests use pytest markers:
- `smoke` — Quick validation (runs on all environments)
- `qa` — Regression tests (runs on QA)
- `load` — Performance tests (runs on QA)

```bash
pytest tests/ -v -m "smoke"        # Smoke only
pytest tests/ -v -m "qa or load"   # QA + load
pytest tests/ -v                   # All tests
```

## Tools & Versions

| Tool | Version | Purpose |
|------|---------|---------|
| schemachange | 3.7.0 | Database migration engine |
| sqlfluff | 3.0.0 | SQL linting (Snowflake dialect) |
| pytest | 7.4.4 | Test framework |
| snowflake-connector-python | 3.6.0 | Snowflake connectivity |
| Python | 3.11 | Runtime |
