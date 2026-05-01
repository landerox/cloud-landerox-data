# System Architecture

## Purpose

This document defines the architecture stance for `cloud-landerox-data` and separates:

- What is implemented today (`As-Is`)
- What is planned next (`Target`)
- How decisions are made per source/domain (decision matrix)

## As-Is

- Runtime folders are present but not populated yet:
  - `functions/ingestion/`
  - `functions/trigger/`
  - `dataflow/pipelines/`
- Runtime implementations are intentionally excluded from this public baseline.
- Shared infrastructure utilities are implemented in `shared/common/`.
- CI validates quality and tests; deployment workflows are not yet active.
- This repository is intentionally maintained as a public architecture/template baseline.
- Production-specific pipelines and deployment details may live in private repos.

## Target Architecture

The target is a **hybrid GCP data platform**:

- **Warehouse path** for fast SQL analytics on BigQuery native tables.
- **Lakehouse path** for open-format interoperability on GCS/BigLake.
- **Batch + Streaming coexistence** as a practical operating model.
- **Medallion layering** (`Bronze -> Silver -> Gold`) for data quality progression.
- **Governed operation** with contracts, replay paths, quality gates, and SLOs.

The mermaid renderings of the target topology and the reference E2E
flow with controls live in the diagram catalog so they have a single
source of truth:

- [Context overview](diagrams/01-context-overview.md) — sources →
  ingestion → Pub/Sub/Bronze → Dataflow → BigQuery Silver/Gold (+
  optional BigLake/Iceberg, optional CDC).
- [End-to-end with controls](diagrams/02-e2e-controls.md) — adds
  contract validation, DLQ + replay, data quality gates, and the
  observability/SLO touch points.

## Diagram set

The canonical set is defined in [diagrams/README.md](diagrams/README.md),
including when to use one vs two diagrams for Dataflow and Cloud
Functions views. Direct links to each template:

- [Diagram Catalog](diagrams/README.md)
- [Dataflow Shared](diagrams/03-dataflow-shared.md)
- [Dataflow Streaming](diagrams/03a-dataflow-streaming.md)
- [Dataflow Batch/Replay](diagrams/03b-dataflow-batch-replay.md)
- [Functions Shared](diagrams/04-functions-shared.md)
- [Functions Ingestion HTTP/Webhook](diagrams/04a-functions-ingestion-http.md)
- [Functions Trigger/Orchestration](diagrams/04b-functions-trigger-orchestration.md)
- [Storage Hybrid BigQuery + Lakehouse](diagrams/05-storage-hybrid-bq-lakehouse.md)

## Architecture Vocabulary (Scope Clarification)

- **Architecture patterns:** Event-driven, batch/stream hybrid, Medallion, selective Kappa/Lambda.
- **Cross-cutting patterns:** Data contracts, schema evolution, idempotency, deduplication, quality gates, replay.
- **Organizational model:** Data Mesh (team/domain ownership), optional for this personal repo.
- **Services:** Cloud Functions, Pub/Sub, Dataflow, BigQuery, GCS, BigLake.
- **Formats:** JSON/NDJSON, Avro, Parquet.
- **Table formats:** BigQuery native tables, Apache Iceberg (primary external table format), Delta/Hudi only when interoperability requires them.

## Minimum patterns (must-have)

1. **Data Contracts + Schema Evolution**
   Contract versioning (`schema_version`) and compatibility policy (backward/forward) per source.
2. **DLQ + Replay/Backfill**
   Invalid records route to DLQ with reason codes and deterministic replay path.
3. **Idempotency + Deduplication**
   Stable event keys (for example `event_id`) and explicit dedup windows or merge keys.
4. **Data Quality Gates**
   Checks at Bronze -> Silver and Silver -> Gold boundaries.
5. **Observability + SLO**
   Track latency, error rate, freshness, and processed volume.
6. **Orchestration**
   Cloud Scheduler and/or Workflows for batch runs, backfills, and re-runs.
7. **CDC pattern (conditional)**
   Add only when transactional database sources are in scope.
8. **Governance**
   PII classification, retention policy, and dataset/table access controls.

## GCP implementation mapping

| Pattern | Typical GCP implementation |
| :--- | :--- |
| Data contracts + schema evolution | JSON schema in repo, Pub/Sub schema validation (when applicable), BigQuery schema versioning strategy |
| DLQ + replay/backfill | Pub/Sub dead-letter topics/subscriptions, Dataflow error side outputs, replay jobs via Dataflow batch |
| Idempotency + deduplication | Cloud Function idempotency keys, Dataflow key/window dedup, BigQuery merge keys |
| Data quality gates | Validation transforms in Dataflow, SQL checks in BigQuery, quality checks at Bronze->Silver and Silver->Gold |
| Observability + SLO | Cloud Logging structured logs, Cloud Monitoring metrics/alerts, error budget/SLO dashboards |
| Orchestration | Cloud Scheduler + Workflows for schedules, retries, backfills, and re-runs |
| CDC pattern (conditional) | Datastream (or source-native CDC) + Dataflow/BigQuery ingestion path |
| Governance | BigQuery IAM policies, dataset/table ACLs, retention configuration, data classification and catalog metadata |

## Optional patterns

1. **Data Mesh**
   Organizational scaling pattern; useful if multi-team ownership emerges.
2. **Databricks/Delta interoperability**
   Keep optional for cross-platform use cases; not core for current GCP-first runtime.

## Repository model

- **Public repo (`cloud-landerox-data`)**: reference architecture, patterns, templates, and shared engineering practices.
- **Infrastructure repo (Terraform, separate)**: GCP provisioning and environment setup.
- **Private runtime repos (optional)**: production pipeline logic, environment-specific deployments, and sensitive operational details.

## Scalable runtime organization (recommended for GCP)

For runtimes with many modules (for example, 50+ pipelines), use this structure in
the private runtime repo:

```bash
runtime-data-platform/
├── functions/
│   ├── ingestion/
│   │   └── <domain>/<source>_<mode>/
│   │       └── main.py
│   └── trigger/
│       └── <domain>/<event>_<purpose>/
│           └── main.py
├── dataflow/
│   └── pipelines/
│       └── <domain>/
│           ├── bronze/<pipeline_name>/
│           ├── silver/<pipeline_name>/
│           └── gold/<pipeline_name>/
└── tests/
    ├── functions/<domain>/...
    └── dataflow/<domain>/...
```

Why this layout is aligned with GCP operating reality:

- Keeps deployment blast radius small (one function/pipeline per module folder).
- Maps naturally to Medallion responsibilities in BigQuery/GCS.
- Supports independent scaling and rollback per pipeline.
- Works with path-based CI/CD triggers for selective deployments.

## Adoption plan (to avoid overload)

These phases describe the order in which to bring up patterns inside a
**private runtime repository**, not the maturity of this baseline
itself. The cross-cutting primitives (contracts, DLQ, retry, metrics,
trace propagation) already ship in `shared/common/` -- a runtime team
just wires them in the order below.

- **Phase 1 (start):** Contracts, DLQ, idempotency, base observability.
- **Phase 2:** Quality gates, replay automation, orchestration hardening.
- **Phase 3:** CDC (if needed), governance expansion, optional interoperability patterns.

## Decision Matrix

| Decision axis | Preferred option | Alternate option | Use when |
| :--- | :--- | :--- | :--- |
| Ingestion entry | API/Event -> Pub/Sub | API/Event -> GCS direct | Pub/Sub for resilience/backpressure; direct GCS for low-frequency archival |
| Processing mode | Streaming | Batch | Streaming for low-latency SLAs; batch for backfill/scheduled loads |
| Silver storage | BigQuery native | GCS + BigLake (Iceberg/Parquet/Avro) | BigQuery native for SQL-first speed; BigLake for open-format interoperability |
| Transformation style | SQL ELT | Dataflow ETL | ELT for business logic in SQL; ETL for complex parsing/enrichment/dedup |
| Topology style | Selective Kappa | Lambda-lite split | Kappa when one logic path is feasible; Lambda-lite when stream and batch constraints differ |
| Contract strategy | Backward-compatible evolution | Breaking change with migration | Backward-compatible by default; migration only when required |
| Replay strategy | DLQ replay | Full backfill reprocessing | DLQ replay for scoped errors; full backfill for systemic issues |
| Governance level | Dataset/table IAM + retention | Domain-level policy stack | Basic controls by default; expand with complexity |

## What this repo is not

- Not a pure Kappa-only platform.
- Not a pure lakehouse-only platform.
- Not a Data Mesh platform by default.

It is a pragmatic hybrid platform that chooses patterns per source, SLA, and cost profile.

## Related documents

- [CI/CD Guide](cicd.md)
- [Dataflow Guide](guides/dataflow.md)
- [Cloud Functions Guide](guides/functions.md)
- [GCP Project Baseline Guide](guides/gcp-project-baseline.md)
- [Diagram Catalog](diagrams/README.md)
- [ADR Index](adr/)
- [First E2E Blueprint](blueprints/first-e2e-pipeline.md)
- [First Runtime Scope (Step 2)](blueprints/first-runtime-scope.md)
- [Step 3 Private Runtime Checklist](blueprints/step-3-private-runtime-checklist.md)
