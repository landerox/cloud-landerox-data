# CI/CD Guide

## Scope

This guide reflects the **current CI/CD reality** of this repository and the planned next steps.

Project bootstrap prerequisites (APIs + IAM identities) are documented in:
[GCP Project Baseline Guide](guides/gcp-project-baseline.md).

## Current CI (As-Is)

### Active workflows

- `.github/workflows/lint.yml` — quality gate (lint, type, test + coverage,
  security including dependency audit and license compliance).
- `.github/workflows/codeql.yml` — SAST analysis (push/PR + weekly schedule).
- `.github/workflows/semgrep.yml` — Semgrep SAST with `p/python`,
  `p/security-audit`, `p/secrets` rulesets (push/PR + weekly + manual);
  SARIF uploaded to the Security tab.
- `.github/workflows/scorecard.yml` — OpenSSF Scorecard (weekly + on push to
  `main`); SARIF uploaded to the Security tab and results published to the
  public Scorecard dashboard.
- `.github/workflows/trivy.yml` — Trivy IaC config scan (every PR/push that
  touches `.devcontainer/**` or workflows; blocking on CRITICAL/HIGH) and
  Trivy image scan of the devcontainer base (weekly only; informational).
- `.github/workflows/link-check.yml` — lychee Markdown link checker
  (weekly + manual); opens a tracking issue when a scheduled run fails.
- `.github/workflows/nightly.yml` — `pytest -m "integration or slow"`
  (daily + manual); tolerates "no tests collected" so the gate is wired
  before the first integration test exists.
- `.github/workflows/release.yml` — manual release pipeline: commitizen
  bump, CycloneDX SBOM, SLSA build provenance attestation, GitHub Release.

### Trigger

- `push` to `main`
- `pull_request` targeting `main`
- `workflow_dispatch`
- `workflow_call`

### What it runs

Each job calls `uv sync --frozen` first (uv wheels are cached by `uv.lock` hash).

| Job | Command | Notes |
| :--- | :--- | :--- |
| `lint` | `uv run pre-commit run --all-files --show-diff-on-failure` | `~/.cache/pre-commit` cached by `.pre-commit-config.yaml` hash. |
| `type-check` | `uv run pyright` | Redundant with the pre-commit `pyright` hook; kept as an independent status check. |
| `test` | `uv run pytest --cov --cov-report=term-missing --cov-report=xml` | Enforces `fail_under = 90` on `shared/**` (configured in `pyproject.toml`). Uploads XML to Codecov and as a workflow artifact. |
| `security` | `uv run pip-audit` + `pip-licenses` → `.github/scripts/check_licenses.py` | `gitleaks` already runs via pre-commit in `lint`. License gate fails CI on copyleft (GPL/AGPL/LGPL/SSPL/EUPL) or unknown licenses; allowlist lives in the script. |

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

## Versioning

Release cadence, the pre-1.0 stance, the 1.0 graduation criteria, and
the breaking-change policy live in [versioning.md](versioning.md).

## Definition of done for new workflows

A new CI/CD workflow should only be considered active when:

- The workflow file exists in `.github/workflows/`
- It passes in `main`
- It is referenced in this document
- Required secrets/variables are documented in the same PR

## Branch protection (recommended settings)

Configure these on `main` so the gates above are not bypassable. GitHub
path: **Settings → Rules → Rulesets** (or legacy **Settings → Branches →
Branch protection rules**).

### Required status checks

Mark these checks **required**, with "Require branches to be up to date
before merging" enabled:

| Check name (as it appears in the PR UI) | Source workflow |
| :--- | :--- |
| `Lint` | `lint.yml` |
| `Type Check` | `lint.yml` |
| `Test` | `lint.yml` |
| `Security` | `lint.yml` |
| `Analyze (python)` | `codeql.yml` |

The `Analyze` check from `scorecard.yml` is informational; leave it
unrequired unless you want a failed score to block merges. The nightly,
link-check, and release workflows are not PR-scoped and must not be
required.

### Recommended rules

- **Require a pull request before merging** with at least 1 approving
  review.
- **Dismiss stale pull request approvals when new commits are pushed.**
- **Require conversation resolution before merging.**
- **Require linear history** (we use Conventional Commits and the
  changelog generator assumes a linear log).
- **Block force pushes** and **restrict deletions** on `main`.

### Caveat for the release workflow

`release.yml` pushes the bump commit and tag back to `main` using
`GITHUB_TOKEN`. If "Require a pull request before merging" is enforced
on `main` without an exception, the push will be rejected. Two options:

1. **Bypass list:** add `github-actions[bot]` (or a dedicated release
   PAT identity) to the ruleset bypass list.
2. **PR-based release:** change `release.yml` to open a release PR
   instead of pushing directly. Trade-off: you lose the single-click
   release UX.

If you also enable **require signed commits**, the `github-actions[bot]`
identity will not satisfy it; switch to a PAT or to a release-bot SSH
key configured for signing.
