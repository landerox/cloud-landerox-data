# cloud-landerox-data

[![CI](https://github.com/landerox/cloud-landerox-data/actions/workflows/lint.yml/badge.svg)](https://github.com/landerox/cloud-landerox-data/actions/workflows/lint.yml)
[![CodeQL](https://github.com/landerox/cloud-landerox-data/actions/workflows/codeql.yml/badge.svg)](https://github.com/landerox/cloud-landerox-data/actions/workflows/codeql.yml)
[![codecov](https://codecov.io/gh/landerox/cloud-landerox-data/branch/main/graph/badge.svg)](https://codecov.io/gh/landerox/cloud-landerox-data)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/landerox/cloud-landerox-data/badge)](https://scorecard.dev/viewer/?uri=github.com/landerox/cloud-landerox-data)
[![SLSA Level 3](https://slsa.dev/images/gh-badge-level3.svg)](https://slsa.dev)
[![Python 3.13](https://img.shields.io/badge/python-3.13-3776AB?logo=python&logoColor=white)](https://www.python.org/downloads/release/python-3130/)
[![Checked with pyright](https://img.shields.io/badge/pyright-checked-0E7FC0?logo=python&logoColor=white)](https://github.com/microsoft/pyright)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Conventional Commits](https://img.shields.io/badge/Conventional%20Commits-1.0.0-FE5196?logo=conventionalcommits&logoColor=white)](https://www.conventionalcommits.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![GCP](https://img.shields.io/badge/GCP-Ready-4285F4?logo=google-cloud&logoColor=white)](https://cloud.google.com/)

> **Public GCP Data Architecture Baseline: Hybrid Warehouse/Lakehouse with Batch + Streaming**

## What this repository is

This repository contains architecture guidance, standards, diagram templates, and
folder placeholders for GCP data platforms:

- Event-driven ingestion patterns with Cloud Functions + Pub/Sub
- Stream and batch processing patterns with Dataflow (Apache Beam)
- Data organization patterns with Bronze/Silver/Gold conventions on GCS + BigQuery
- Architecture documentation and pattern placeholders for pipeline design decisions
- Alignment with a separate Terraform infrastructure repository for GCP provisioning

Scope note:

- This repository does not host production runtime implementations.
- Production runtime code is expected in private runtime repositories.
- Infrastructure provisioning is expected in a separate Terraform repository.

## Current status

- Production folders are documented placeholders — wiring rules, naming
  conventions, and runbook hooks are in their READMEs, ready for a
  private runtime repo to fill in:
  - `functions/ingestion/`
  - `functions/trigger/`
  - `dataflow/pipelines/`
- Runtime modules are intentionally not implemented in this public baseline.
- A minimal **public runtime example** that imports this baseline as a
  dependency and wires one end-to-end pipeline (DirectRunner +
  Pub/Sub emulator) lives in
  [landerox/cloud-landerox-runtime-example](https://github.com/landerox/cloud-landerox-runtime-example).
  Use it as the starting point for a private runtime repo.
- CI runs an extended suite of gates on every PR and scheduled jobs:
  ruff, pyright, pytest (with coverage), CodeQL, Semgrep, pip-audit,
  license allowlist, Trivy IaC, OpenSSF Scorecard, lychee link check,
  mutation testing (informational, nightly), and property-based tests
  with hypothesis.
- Releases (`release.yml`) bump the version with commitizen, attach a
  CycloneDX SBOM and a SLSA build-provenance attestation to the
  GitHub Release.
- This repository is maintained as a **public baseline** (docs, patterns, templates).
- Concrete production pipelines should live in private runtime repositories per
  project context.

## Architecture stance

This project is intentionally **hybrid**, not pure Kappa or pure Lambda:

- Use warehouse-first patterns when BigQuery native tables are fastest to deliver value.
- Use lakehouse patterns (BigLake + open formats) when interoperability and file-based processing matter.
- Run streaming and batch side by side; choose per source SLA, data shape, and cost profile.
- Treat Data Mesh as an organizational model, not a mandatory runtime pattern for this repo.
- Apply cross-cutting controls: data contracts, schema evolution, DLQ/replay, idempotency, quality gates, observability/SLO, and governance baselines.

See the full decision model in [docs/architecture.md](docs/architecture.md).

## Reference technology map

| Category | Technologies in scope |
| :--- | :--- |
| Processing | Cloud Functions, Pub/Sub, Dataflow |
| Storage & query | GCS, BigQuery, BigLake |
| Table formats | Apache Iceberg (primary lakehouse table format), BigQuery native tables |
| File formats | JSON/NDJSON, Avro, Parquet |
| Optional ecosystem | Databricks/Delta interoperability considered when required by source/domain |

## Repository structure

| Directory | Purpose |
| :--- | :--- |
| `functions/` | Cloud Function folder structure placeholders (public baseline) |
| `dataflow/` | Beam pipeline folder structure placeholders (public baseline) |
| `shared/common/` | Shared infrastructure utilities: I/O factories, structured logging with W3C trace propagation, OpenTelemetry tracing → Cloud Trace, Secret Manager access, contract validation, DLQ helpers, retry decorator, Beam metrics, typed exception hierarchy |
| `tests/` | Unit/integration tests mirroring source layout |
| `docs/` | Architecture, CI/CD, and engineering guidance |

## Scaling guidance (recommended)

For medium/large runtimes (for example, ~50 pipelines) in GCP:

- **Dataflow:** organize by `domain -> layer (bronze/silver/gold) -> pipeline module`.
- **Functions:** keep `ingestion/` and `trigger/`, then group by domain and
  source/event purpose.
- **CI/CD:** avoid one mega deploy pipeline; use shared CI plus selective CD by
  changed module in private runtime repos.

See details in:

- [System Architecture](docs/architecture.md)
- [Diagram Catalog](docs/diagrams/README.md)
- [Dataflow Guide](docs/guides/dataflow.md)
- [Cloud Functions Guide](docs/guides/functions.md)
- [CI/CD Guide](docs/cicd.md)

## Getting started

### Prerequisites

- Python 3.13
- [`uv`](https://docs.astral.sh/uv/)
- [`just`](https://github.com/casey/just#installation)

### Setup

```bash
just sync
just pre-commit-install
```

### Quality checks

```bash
just lint
just type
just test
```

## Documentation

Architecture and process:

- [Architecture Guide](docs/architecture.md)
- [Architecture Decisions (ADRs)](docs/adr/README.md)
- [CI/CD Guide](docs/cicd.md)
- [Versioning Policy](docs/versioning.md)
- [Tech Stack](docs/tech-stack.md)

Engineering guides:

- [Coding Style](docs/guides/coding-style.md)
- [Testing](docs/guides/testing.md)
- [Error Handling and DLQ](docs/guides/error-handling.md)
- [Observability and SLOs](docs/guides/observability.md)
- [Security (developer)](docs/guides/security.md)
- [Cloud Functions Guide](docs/guides/functions.md)
- [Dataflow Guide](docs/guides/dataflow.md)
- [GCP Project Baseline Guide](docs/guides/gcp-project-baseline.md)

Diagrams and blueprints:

- [Diagram Catalog](docs/diagrams/README.md)
- [First E2E Blueprint](docs/blueprints/first-e2e-pipeline.md)
- [First Runtime Scope (Step 2)](docs/blueprints/first-runtime-scope.md)
- [Step 3 Private Runtime Checklist](docs/blueprints/step-3-private-runtime-checklist.md)

## Contributing

See [CONTRIBUTING.md](.github/CONTRIBUTING.md) for the development
workflow, naming conventions, and PR checklist. Behavior in this
repository follows our [Code of Conduct](.github/CODE_OF_CONDUCT.md).

## Security

Report vulnerabilities privately via the process in
[SECURITY.md](.github/SECURITY.md). For developer-facing security
rules (secrets, SQL, PII, dependencies), see
[docs/guides/security.md](docs/guides/security.md).

## Changelog

Release history is tracked in [CHANGELOG.md](CHANGELOG.md), following
[Keep a Changelog](https://keepachangelog.com/) and
[Semantic Versioning](https://semver.org/) (see
[docs/versioning.md](docs/versioning.md) for the full policy).

## License

This project is open-source and available under the MIT License. See [LICENSE](LICENSE).
