# Security Policy & Secret Management

## Secret Rotation
- Rotate all Snowflake and GitHub secrets at least every 90 days.
- Remove unused or stale secrets from GitHub repository settings.
- Use unique, strong passwords for all Snowflake users and roles.
- Store secrets only in GitHub Actions Secrets, never in code or plaintext files.

## Adding/Updating Secrets
1. Go to your repository → Settings → Secrets and variables → Actions.
2. Click "New repository secret" and add/update the required secret (e.g., `SF_PASSWORD`).
3. Remove or update secrets when users leave the team or roles change.

## Auditing & Monitoring
- Enable GitHub audit logs for secret access and workflow runs.
- Review workflow logs for unauthorized access attempts.
- Use branch protection and required reviewers for production workflows.

## Reporting a Vulnerability
If you discover a security issue, please email the maintainers or open a private security advisory on GitHub. Do not disclose vulnerabilities publicly until resolved.
