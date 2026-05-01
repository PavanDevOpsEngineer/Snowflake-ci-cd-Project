# Snowflake CI/CD Pipeline with schemachange & GitHub Actions

Automated database schema change management across **Dev → QA → Prod** environments for Snowflake, powered by [schemachange](https://github.com/Snowflake-Labs/schemachange) and GitHub Actions.

## 🎯 Project Objective
Design a CI/CD pipeline that automates Snowflake schema changes — validation, testing, deployment, and rollback — without affecting production stability.

## 🧱 Architecture Overview
```
Developer ──push──► GitHub Repo ──► GitHub Actions
                                       │
                                       ├── Lint / Validate SQL
                                       ├── Deploy to DEV  (auto)
                                       ├── Run Tests (dev)
                                       ├── Deploy to QA   (auto on develop branch)
                                       ├── Run Tests (qa)
                                       └── Deploy to PROD (manual approval, main branch)
                                              │
                                       Metadata Table: SCHEMACHANGE.CHANGE_HISTORY
```

## ⚡️ Python Dependency Caching
This project uses GitHub Actions caching for pip dependencies to speed up CI/CD runs. The cache is keyed on OS and requirements.txt hash.

## 🧹 Pre-commit SQL Linting
SQL files in `migrations/` are automatically linted using [sqlfluff](https://github.com/sqlfluff/sqlfluff) (Snowflake dialect) via pre-commit hooks and in CI. To enable locally:

```sh
pip install pre-commit sqlfluff
pre-commit install
# Lint all SQL files
pre-commit run sqlfluff-lint --all-files
```

## 🔒 Security & Secret Management
- All Snowflake and workflow secrets are stored in GitHub Actions Secrets (never in code).
- Rotate secrets at least every 90 days. See [SECURITY.md](SECURITY.md) for policy and instructions.

## 📂 Repository Structure
```
snowflake-cicd/
├── migrations/
│   ├── V1.1__initial/             # Versioned change scripts (run once)
│   ├── V1.2__add_customer_table/
│   ├── V1.3__add_orders_table/
│   ├── R__views/                  # Repeatable (re-run on change)
│   └── R__procedures/
├── rollback/                      # Manual rollback SQL scripts
├── tests/                         # Python validation/regression tests
├── scripts/                       # Helper bash/python automation
├── .github/workflows/             # CI/CD pipelines
│   ├── ci-validate.yml            # Lint + dry-run on PRs
│   ├── cd-dev.yml                 # Auto-deploy to DEV
│   ├── cd-qa.yml                  # Auto-deploy to QA
│   └── cd-prod.yml                # Gated deploy to PROD
└── docs/                          # Architecture diagrams, runbooks
```

## 🚀 Quick Start

### 1. Configure GitHub Secrets
Add these at **Settings → Secrets and variables → Actions**:

| Secret | Description |
| --- | --- |
| `SF_ACCOUNT`   | Snowflake account identifier (e.g. `xy12345.ap-south-1`) |
| `SF_USER`      | Service account username |
| `SF_PASSWORD`  | Service account password |
| `SF_ROLE`      | Deploy role (e.g. `CICD_DEPLOYER_ROLE`) |
| `SF_WAREHOUSE` | Warehouse (e.g. `CICD_WH`) |
| `SF_DB_DEV` / `SF_DB_QA` / `SF_DB_PROD` | Target databases per environment |

### 2. Add a Migration
Create a file under `migrations/` following the naming rule:
```
V<major>.<minor>__<description>.sql    # versioned, runs once
R__<description>.sql                   # repeatable, runs when hash changes
```

### 3. Push & Merge
- PR → triggers **ci-validate.yml** (lint + dry-run)
- Merge to `develop` → auto-deploy to **DEV** + **QA**
- Merge to `main` → deploy to **PROD** (requires manual approval)

## 🔁 Rollback Strategy
1. Every deploy is tracked in `SCHEMACHANGE.CHANGE_HISTORY`.
2. Corresponding down-scripts live in `rollback/` with the same version number.
3. Trigger workflow `cd-prod.yml` with input `action=rollback` & `target_version=Vx.y`.

## 📊 Monitoring
- Query `QUERY_HISTORY` for deploy duration & failures.
- Slack notifications on every workflow via `SLACK_WEBHOOK_URL` secret (optional).

## 🧪 Testing
```bash
pip install -r tests/requirements.txt
pytest tests/ -v
```

## 📜 License
MIT – for academic / portfolio use.
