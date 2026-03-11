---
name: deployment
description: Docker, CI/CD pipelines, deployment strategies, and infrastructure. Use for deploying to Pi, Docker, cloud, or setting up pipelines.
disable-model-invocation: true
---

# Deployment

## Pipeline Stages
1. **Test** — run full test suite, fail if tests fail
2. **Lint** — ruff/eslint/clippy, fail on errors
3. **Pre-commit** — run pre-commit hooks if configured
4. **Commit** — stage + commit with descriptive message
5. **Push** — push to remote
6. **Deploy** — rsync/docker/cloud deploy
7. **Verify** — run smoke tests on target

## Docker
- Multi-stage builds: builder stage + slim runtime stage
- Pin base image versions (not `latest`)
- Non-root user in production containers
- Health checks: `HEALTHCHECK CMD curl -f http://localhost/health || exit 1`
- `.dockerignore` always: `.git`, `node_modules`, `__pycache__`, `.env`

## CI/CD
- GitHub Actions: use `actions/checkout@v4`, cache dependencies, matrix for multi-version
- Secrets: never hardcode, use `${{ secrets.NAME }}`, rotate quarterly
- Deploy gates: require passing tests + review approval

## Secrets Management
- Never commit secrets. Use `.env` (gitignored) + environment variables.
- For production: vault/SSM/sealed-secrets, not env files.
