# CI/CD Guide

## Scope

This guide reflects the **current CI/CD reality** of this repository and the planned next steps.

Project bootstrap prerequisites (APIs + IAM identities) are documented in:
[GCP Project Baseline Guide](guides/gcp-project-baseline.md).

## Current CI (As-Is)

### Active workflow

- `.github/workflows/lint.yml`

### Trigger

- `push` to `main`
- `pull_request` targeting `main`
- `workflow_dispatch`
- `workflow_call`

### What it runs

1. `uv sync --frozen`
2. `uv run pre-commit run --all-files`
3. `uv run pip-audit`
4. `uv run pytest`

This is currently a **quality gate pipeline**, not a deployment pipeline.

## Planned CD (Target, not active yet)

If runtime modules are added to this public repo, typical CD targets are:

- Selective deployment for Cloud Functions by changed folder.
- Dataflow Flex Template build/publish workflow for production pipelines.
- Environment-specific release gates (`dev` -> `stg` -> `prd` if needed).

If production runtime modules stay private, this repo can remain CI-only by design.

Until those workflows exist, treat deployment sections in older docs as aspirational.

## Recommended topology for private runtime repos

For a runtime with many modules (for example, ~50 pipelines), use this default:

- **Shared CI for all modules** (lint, type, test, security).
- **Selective CD per changed module path** (no full-repo deploy on every merge).
- **Separate workflow families by runtime type**:
  - `functions-deploy.yml` for `functions/**`
  - `dataflow-deploy.yml` for `dataflow/pipelines/**`

This provides fast feedback and small blast radius while keeping one engineering
baseline.

## Mega CD vs independent CD

Use this decision rule:

| Option | Recommendation | Use when |
| :--- | :--- | :--- |
| Single mega deploy workflow for all modules | Avoid as default | Only for very small runtimes with tightly coupled release cadence |
| Shared CI + selective CD (path-based matrix) | **Default** | Most GCP data platforms with many independent functions/pipelines |
| Fully independent CI/CD per domain repo | Conditional | Separate teams, strict compliance boundaries, or very different release cadences |

## Path-based deployment model (default)

1. Detect changed module roots (for example each pipeline/function folder).
2. Build/deploy only those modules.
3. Promote artifacts across environments with approvals.
4. Run scheduled full regression/nightly validation separately.

This prevents long deploy queues and unnecessary runtime restarts.

## Local parity commands

```bash
just sync
just lint
just type
just test
uv run pre-commit run --all-files
```

## Secrets and configuration

No deployment secrets are required by the current active CI workflow.

When CD is introduced, prefer:

- Workload Identity Federation (WIF)
- Environment-scoped GitHub Secrets/Variables
- No static service account keys in repository or CI logs

## Definition of done for new workflows

A new CI/CD workflow should only be considered active when:

- The workflow file exists in `.github/workflows/`
- It passes in `main`
- It is referenced in this document
- Required secrets/variables are documented in the same PR
