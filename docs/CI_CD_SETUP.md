# CI/CD Configuration Guide

**Status:** ✅ Production-ready CI/CD pipelines configured

## Overview

This project includes comprehensive CI/CD pipelines using GitHub Actions for automated testing, code quality checks, Docker builds, and security scanning.

---

## Workflow Files

### 1. **tests.yml** — Test & Coverage Pipeline
**Triggers:** `push`, `pull_request`, `schedule` (daily at 2 AM UTC)

**Jobs:**
- `test` — Run pytest across Python 3.10, 3.11, 3.12
  - Unit tests with coverage reporting
  - Coverage uploaded to Codecov
  - Test results archived (30-day retention)
  
- `integration-test` — Test CLI commands
  - `python cli.py predict`
  - `python cli.py optimize`
  - `python cli.py report`
  - `python cli.py evaluate`

- `test-summary` — Final status check

**Outputs:**
- JUnit XML test results
- HTML coverage reports
- Codecov integration

### 2. **docker.yml** — Docker Build & Push Pipeline
**Triggers:** `push` (main/master + tags), `pull_request`, `workflow_dispatch`

**Jobs:**
- `build` — Build and push Docker image
  - Multi-platform support (Linux/ARM64/x86)
  - BuildKit caching optimization
  - Semantic versioning tags
  - GitHub Container Registry or Docker Hub

- `scan` — Security vulnerability scanning
  - Trivy vulnerability scanner
  - SARIF results uploaded to GitHub Security tab
  - Only on pushes (not PRs)

- `verify` — Verify built image
  - Test with docker-compose
  - Run CLI predictions
  - Validates image functionality

**Outputs:**
- Docker image pushed to registry
- Security scan reports
- Build verification passed

### 3. **quality.yml** — Code Quality Pipeline
**Triggers:** `push`, `pull_request`

**Jobs:**
- `lint` — Black, isort, Flake8
  - Code formatting check (Black)
  - Import sorting (isort)
  - Linting (Flake8 with extensions)
  - Non-blocking (continue-on-error)

- `type-check` — mypy static type checking
  - Validates type annotations
  - Ignores missing type stubs
  - Non-blocking

- `security` — Bandit security scanning
  - Detects common security issues
  - Reports to artifacts

- `dependencies` — Dependency audit
  - pip-audit for known vulnerabilities
  - Validates all dependencies

- `code-metrics` — Pylint & Radon
  - Code complexity analysis
  - Maintainability index
  - Non-blocking

**Outputs:**
- Quality reports (non-blocking)
- Security scan results
- Dependency audit reports

### 4. **ci.yml** — Legacy CI Pipeline (Existing)
**Original workflow** — Maintained for compatibility
- Tests across Python versions
- CLI validation
- Docker build verification

---

## Setup Instructions

### Prerequisites

1. **GitHub Secrets** (for Docker Hub push):
   ```
   DOCKER_USERNAME: <your-docker-hub-username>
   DOCKER_PASSWORD: <your-docker-hub-token>
   ```

2. **Install locally (optional):**
   ```bash
   # Pre-commit hooks
   pip install pre-commit
   pre-commit install
   
   # Test dependencies
   pip install -r requirements-dev.txt
   ```

### Local Testing

**Run tests locally before push:**
```bash
# All tests
pytest tests/ -v --cov=src --cov-report=term-missing

# Code quality
black --check src/
flake8 src/
mypy src/ --ignore-missing-imports

# Pre-commit
pre-commit run --all-files
```

### Push to Trigger CI

```bash
# Push to main → triggers all workflows
git push origin main

# Create a tag → triggers Docker build
git tag v1.0.0
git push origin v1.0.0
```

---

## GitHub Secrets Configuration

### Required Secrets

**For Docker Hub Push:**
```yaml
DOCKER_USERNAME: your-docker-username
DOCKER_PASSWORD: your-docker-hub-token  # Use Personal Access Token
```

**For GitHub Container Registry (optional):**
No secrets needed — uses `GITHUB_TOKEN` automatically

### Set Secrets in GitHub

1. Go to **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret**
3. Add `DOCKER_USERNAME` and `DOCKER_PASSWORD`

---

## Pre-Commit Hooks

**Install locally:**
```bash
pip install pre-commit
pre-commit install
```

**Run manually:**
```bash
# All files
pre-commit run --all-files

# Specific hook
pre-commit run black --all-files
pre-commit run flake8 --all-files
```

**Hooks included:**
- ✅ Black formatting
- ✅ isort import sorting
- ✅ Flake8 linting
- ✅ mypy type checking
- ✅ Bandit security
- ✅ Trailing whitespace
- ✅ YAML/JSON validation
- ✅ Merge conflict detection
- ✅ Spell checking

---

## Docker BuildKit Configuration

**Located:** `.docker/config.json`

**Settings:**
- Garbage collection: 30 days + 5GB cache limit
- Inline cache enabled
- Network: host

**Enable BuildKit (if not default):**
```bash
export DOCKER_BUILDKIT=1
docker build -t image:tag .
```

---

## Workflow Status & Badges

**Add to README.md:**
```markdown
[![Tests](https://github.com/YOUR_ORG/658/actions/workflows/tests.yml/badge.svg)](https://github.com/YOUR_ORG/658/actions/workflows/tests.yml)
[![Docker Build](https://github.com/YOUR_ORG/658/actions/workflows/docker.yml/badge.svg)](https://github.com/YOUR_ORG/658/actions/workflows/docker.yml)
[![Code Quality](https://github.com/YOUR_ORG/658/actions/workflows/quality.yml/badge.svg)](https://github.com/YOUR_ORG/658/actions/workflows/quality.yml)
```

---

## Pipeline Performance

### Test Pipeline (~5-10 minutes)
- Setup Python: 20s
- Install deps: 60s
- Lint: 30s
- Type check: 40s
- Unit tests: 2-3 min
- Integration tests: 1-2 min
- Upload reports: 30s

### Docker Pipeline (~10-15 minutes)
- Setup BuildKit: 20s
- Build image: 5-7 min (cached: 1-2 min)
- Security scan: 2-3 min
- Verify image: 1-2 min

### Quality Pipeline (~5-8 minutes)
- Lint checks: 1 min
- Type check: 1 min
- Security scan: 1 min
- Dependency audit: 1 min
- Code metrics: 1-2 min

---

## Troubleshooting

### Docker Build Fails
```
❌ Docker build action failed
```
**Solution:**
1. Check `.dockerignore` — ensure no needed files excluded
2. Verify `Dockerfile` syntax: `docker build -t test .`
3. Check BuildKit cache: `docker builder prune`

### Tests Fail Locally But Pass in CI
```
❌ ImportError: cannot import name 'X'
```
**Solutions:**
1. Clear cache: `python -m pytest --cache-clear`
2. Reinstall: `pip install -r requirements-dev.txt --force-reinstall`
3. Check Python version: `python --version` (must be 3.10+)

### Pre-commit Hooks Block Push
```
❌ pre-commit hook failed
```
**Solutions:**
1. Auto-fix: `black src/` + `isort src/`
2. Review: `flake8 src/`
3. Bypass (not recommended): `git commit --no-verify`

### Docker Push Fails
```
❌ unauthorized: authentication required
```
**Solutions:**
1. Verify secrets are set: GitHub Settings → Secrets
2. Check token expiry: Regenerate if needed
3. Verify username: Echo `${{ secrets.DOCKER_USERNAME }}`

---

## Advanced Configuration

### Modify Triggers

**Run on every push:**
```yaml
on:
  push:
    branches: [ '**' ]  # All branches
```

**Run on PR to any branch:**
```yaml
on:
  pull_request:
    branches: [ '**' ]
```

**Run manually:**
```yaml
on:
  workflow_dispatch:
    inputs:
      reason:
        description: 'Reason for manual trigger'
        required: true
```

### Customize Quality Thresholds

**In `.pre-commit-config.yaml`:**
```yaml
- repo: https://github.com/PyCQA/flake8
  hooks:
    - id: flake8
      args: ['--max-line-length=100', '--max-complexity=10']
```

**In `quality.yml`:**
```yaml
- name: Run Bandit
  run: bandit -r src/ -ll  # Change -ll to -i for more strict
```

---

## Integration with Other Services

### Codecov Integration
```yaml
- uses: codecov/codecov-action@v3
  with:
    files: ./coverage.xml
    flags: unittests
```

**Results:** Coverage reports available at codecov.io

### GitHub Security Tab
Trivy scan results automatically appear in:
GitHub → Security → Code scanning alerts

### Docker Hub Automated Builds (Optional)
Connect Docker Hub to GitHub for automatic image builds:
1. Docker Hub → Repositories → Settings → Linked Accounts
2. Connect GitHub account
3. Enable automatic builds on push

---

## Maintenance

### Regular Tasks

**Monthly:**
- Review workflow performance
- Update action versions
- Check for new security tools

**Quarterly:**
- Update Python versions if new release
- Review and prune old artifacts
- Update dependencies

### Update Actions

```bash
# Check for updates
dependabot check  # GitHub-native

# Manual update
# Edit .github/workflows/*.yml
# Change: uses: docker/setup-buildx-action@v3
#    to:  uses: docker/setup-buildx-action@v4
```

---

## References

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Docker Build Action](https://github.com/docker/build-push-action)
- [Pre-commit Documentation](https://pre-commit.com/)
- [Black Documentation](https://black.readthedocs.io/)
- [Flake8 Documentation](https://flake8.pycqa.org/)

---

**Status:** ✅ CI/CD fully configured and ready for production

**Next Steps:**
1. Set GitHub Secrets (DOCKER_USERNAME, DOCKER_PASSWORD)
2. Push to main → CI/CD pipelines run automatically
3. Monitor workflows in GitHub Actions tab
4. Iterate on feedback and improve
