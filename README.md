# cloud-landerox-data

[![Quality Gates](https://github.com/landerox/cloud-landerox-data/actions/workflows/lint.yml/badge.svg)](https://github.com/landerox/cloud-landerox-data/actions/workflows/lint.yml) ![Python Version](https://img.shields.io/badge/python-3.13+-4285F4.svg) ![Type Check](https://img.shields.io/badge/type--check-ty-blue) ![Security](https://img.shields.io/badge/security-pip--audit-green) [![GCP](https://img.shields.io/badge/GCP-Ready-4285F4?logo=google-cloud&logoColor=white)](https://cloud.google.com/)

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

- Production folders exist but are still placeholders:
  - `functions/ingestion/`
  - `functions/trigger/`
  - `dataflow/pipelines/`
- Runtime modules are intentionally not implemented in this public baseline.
- CI currently runs quality gates (lint, type checks via pre-commit, tests).
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
| `shared/common/` | Shared infrastructure utilities (I/O, logging, secrets) |
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

- Python 3.13+
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

- [Architecture Guide](docs/architecture.md)
- [CI/CD Guide](docs/cicd.md)
- [Architecture Decisions (ADRs)](docs/adr/)
- [Dataflow Guide](docs/guides/dataflow.md)
- [Cloud Functions Guide](docs/guides/functions.md)
- [GCP Project Baseline Guide](docs/guides/gcp-project-baseline.md)
- [Diagram Catalog](docs/diagrams/README.md)
- [First E2E Blueprint](docs/blueprints/first-e2e-pipeline.md)
- [First Runtime Scope (Step 2)](docs/blueprints/first-runtime-scope.md)
- [Step 3 Private Runtime Checklist](docs/blueprints/step-3-private-runtime-checklist.md)

## License

MIT License. See [LICENSE](LICENSE).
