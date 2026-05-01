# AGENTS.md

Single source of truth for AI coding agents working on this repo
(Claude Code, Codex CLI, Gemini CLI, OpenCode, Copilot CLI).
`CLAUDE.md` and `GEMINI.md` are symlinks to this file.

This file is an **index**, not a manual. Details live in `docs/` and adjacent
READMEs. If a topic is missing here, add a dedicated doc under `docs/guides/`
and link it below.

## Project

- **Stack:** Python 3.13, Apache Beam, Cloud Functions, BigQuery, GCS, Pub/Sub, OpenTelemetry (Cloud Trace export).
- **Purpose:** Public baseline (architecture, standards, templates) for GCP
  data platforms. Runtime code lives in private repos.
- **Status:** Quality + supply-chain gates active (lint, type, test,
  CodeQL, Semgrep, Scorecard, Trivy, license, SBOM, hypothesis,
  mutmut, nightly, link-check). Manual `release.yml` cuts versioned
  baselines with SLSA provenance. No deployment of runtime code from
  this repo (intentional).

See [README.md](README.md) for the full overview and
[docs/architecture.md](docs/architecture.md) for the architecture stance.

## Critical rules (non-negotiable)

- Never commit secrets. Read them via `shared.common.get_secret`.
- All Python functions must have type hints.
- Mock external services in tests; never hit real APIs.
- Conventional Commits. Branches: `feat/`, `fix/`, `docs/`, `refactor/`, `chore/`.
- SQL: parameterized queries only.

## Where to find

| Topic | Source |
| :--- | :--- |
| Architecture stance | [docs/architecture.md](docs/architecture.md) |
| Architecture decisions (ADRs) | [docs/adr/README.md](docs/adr/README.md) |
| CI/CD (current and planned) | [docs/cicd.md](docs/cicd.md) |
| Versioning policy (SemVer 2.0.0; pre-1.0 stance and 1.0 graduation criteria) | [docs/versioning.md](docs/versioning.md) |
| Tech stack (tools chosen, why, alternatives) | [docs/tech-stack.md](docs/tech-stack.md) |
| Cloud Functions engineering | [docs/guides/functions.md](docs/guides/functions.md) |
| Dataflow engineering | [docs/guides/dataflow.md](docs/guides/dataflow.md) |
| GCP project bootstrap | [docs/guides/gcp-project-baseline.md](docs/guides/gcp-project-baseline.md) |
| Coding style | [docs/guides/coding-style.md](docs/guides/coding-style.md) |
| Testing standards | [docs/guides/testing.md](docs/guides/testing.md) |
| Error handling and DLQ | [docs/guides/error-handling.md](docs/guides/error-handling.md) |
| Security rules (for developers) | [docs/guides/security.md](docs/guides/security.md) |
| Observability, logging, SLOs | [docs/guides/observability.md](docs/guides/observability.md) |
| Diagrams catalog | [docs/diagrams/README.md](docs/diagrams/README.md) |
| Blueprints (first E2E, scope, handoff) | [docs/blueprints/](docs/blueprints/) |
| Release history | [CHANGELOG.md](CHANGELOG.md) |
| Shared library principles | [shared/README.md](shared/README.md) |
| Test layout and fixtures | [tests/README.md](tests/README.md) |
| Contribution workflow | [.github/CONTRIBUTING.md](.github/CONTRIBUTING.md) |
| Code of Conduct | [.github/CODE_OF_CONDUCT.md](.github/CODE_OF_CONDUCT.md) |
| Pull request template | [.github/PULL_REQUEST_TEMPLATE.md](.github/PULL_REQUEST_TEMPLATE.md) |
| Vulnerability reporting | [.github/SECURITY.md](.github/SECURITY.md) |

## Local workflow

```bash
just sync
just pre-commit-install
just lint
just type
just test
```

See the full `Justfile` for emulator helpers and maintenance recipes.

## When information is missing

If an agent needs guidance that is not covered above, do **not** inline the
answer in this file. Create (or request) a dedicated doc under
`docs/guides/` and link it from the table in this file.
