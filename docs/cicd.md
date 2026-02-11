# CI/CD & Deployment Guide

This repository utilizes **GitHub Actions** for continuous integration and deployment, powered by the **Astral** toolchain for maximum performance and reliability.

## Workflows Overview

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `lint.yml` | PR, Push to main | Code quality validation & Type safety |

---

## 1. Code Quality (`lint.yml`)

**Triggers:** Pull Requests and Pushes to the `main` branch.

**Purpose:** Validates that all code meets the project's strict standards before it can be merged.

**Pipeline Steps:**

1. **Environment Setup:** Python 3.12 with `uv` for deterministic and extremely fast builds.
2. **Dependency Installation:** `uv sync --frozen` ensures the environment exactly matches the lockfile.
3. **Linting & Formatting:** `ruff check .` and `ruff format --check .` enforce PEP8 and consistent styling.
4. **Static Type Analysis:** `ty` performs deep type checking, especially for `NamedTuple` schemas used in Dataflow.
5. **Security Scan:** `detect-secrets` (via pre-commit) scans for leaked credentials or sensitive data.
6. **Unit Tests:** `pytest` executes the test suite with coverage reporting.

**Quality Gate:** A PR cannot be merged if any check fails. We enforce **zero linting warnings** and **zero type errors**.

## 2. SQL Transformations (Dataform)

For ELT patterns, we use **Dataform** to manage SQL-based transformations between Bronze and Silver/Gold layers.

**CI/CD Pipeline for Dataform:**

1. **Compilation:** Dataform code is compiled on every PR to ensure there are no syntax errors or broken dependencies.
2. **Unit Testing & Assertions:** Custom SQL assertions (e.g., uniqueness, non-null checks) are executed to validate data quality before deployment.
3. **Deployment:** Upon merging to `main`, the Dataform compilation result is pushed to the target repository/environment.

---

## Required GitHub Configuration

All secrets and variables must be configured in the **`prd` environment**.

**Location:** Settings → Environments → prd → Environment secrets/variables

### Secrets

| Secret | Description | Used By |
|--------|-------------|---------|
| `GCP_WIF_PROVIDER` | Workload Identity Provider string | All CD workflows |
| `GCP_WIF_SERVICE_ACCOUNT_EMAIL` | Deployment service account | All CD workflows |

### Variables

| Variable | Description | Used By |
|----------|-------------|---------|
| `GCP_PROJECT_ID` | GCP Project ID | All CD workflows |
| `GCP_REGION` | Target GCP region | All CD workflows |
| `GCP_DATAFLOW_TEMPLATE_BUCKET` | GCS bucket for Dataflow Flex Templates | Dataflow workflow |
| `GCP_FUNCTIONS_SOURCE_BUCKET` | GCS bucket for Cloud Functions source code | Functions workflow |

---

## Authentication Model

This project uses **Workload Identity Federation (WIF)** instead of static service account keys, following Google Cloud security best practices.

**Benefits:**

- No long-lived credentials to manage.
- Automatic token rotation.
- Full audit trail in Cloud Logging.

---

## Local Development & Testing

### Running Quality Checks Locally

We mirror the CI environment locally using `uv` and `pre-commit`:

```bash
# 1. Install pre-commit hooks
uv run pre-commit install

# 2. Run all quality checks (Linter + Formatter + Type Checker)
uv run ruff check .
uv run ruff format --check .
uv run ty

# 3. Run unit tests
uv run pytest
```

### Testing Dataflow Locally

```bash
# Run pipeline with DirectRunner for local debugging
uv run python dataflow/pipelines/my-pipeline/pipeline.py \
  --runner=DirectRunner \
  --input_mode=batch \
  --input_path=tests/data/sample.json
```

---

## Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| `ty` error | Type mismatch in NamedTuple | Ensure schema matches BigQuery definition |
| `ruff` failure | Formatting or linting issue | Run `uv run ruff format .` and fix errors |
| Auth failure | WIF misconfigured | Verify the `GCP_WIF_PROVIDER` in GitHub secrets |

### Viewing Logs

```bash
# Function deployment logs
gcloud functions logs read FUNCTION_NAME --region=REGION

# Dataflow job logs
gcloud dataflow jobs list --region=REGION
gcloud dataflow jobs describe JOB_ID --region=REGION
```
