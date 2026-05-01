# Dataflow Pipelines

Placeholder for Apache Beam pipelines (Bronze, Silver, Gold).

## Status

This folder is **intentionally empty in this public baseline.** Production
pipelines live in private runtime repositories. The folder is kept so the
layout, CI, and tooling are wired exactly the way runtime modules will
land.

## What goes here

Domain first, then Medallion layer, then one folder per deployable
pipeline:

```text
pipelines/
└── <domain>/
    ├── bronze/<pipeline_name>/
    │   ├── pipeline.py        # Beam DAG, uses `shared.common.KappaOptions`
    │   ├── schemas.py         # NamedTuple / Pydantic typed records
    │   ├── metadata.json      # Flex Template metadata
    │   ├── requirements.txt   # pipeline-scoped runtime deps
    │   └── README.md          # SLO, schema, deploy params, runbook links
    ├── silver/<pipeline_name>/
    └── gold/<pipeline_name>/
```

`<pipeline_name>` is the canonical naming for a pipeline folder
(e.g. `orders_silver_batch`, `payments_bronze_stream`,
`revenue_gold_daily`). See
[coding-style.md §7](../../docs/guides/coding-style.md#7-naming-conventions).

## Required wiring

Every pipeline must:

- Read inputs via `shared.common.get_source(KappaOptions)` and write via
  `shared.common.get_sink(KappaOptions, schema=...)` so streaming/batch
  selection and BigQuery write method are consistent.
- Use typed schemas (`typing.NamedTuple` or Pydantic models). No
  untyped `dict`s flowing through transforms.
- Validate records via `shared.common.validate_contract` at the
  Bronze→Silver boundary; route `ContractValidationError` records to a
  side output and into a DLQ via
  `shared.common.write_to_gcs_dlq` or `publish_to_pubsub_dlq`.
- Emit the canonical Beam counters via `shared.common.PipelineMetrics`
  under a stable namespace (the pipeline name).
- Mirror tests under
  `tests/dataflow/<domain>/<layer>/<pipeline_name>/test_pipeline.py`
  using `apache_beam.testing.test_pipeline.TestPipeline`.

## Operating model

| Layer | Responsibility |
| :--- | :--- |
| **Bronze** | Ingestion normalization, contract checks, lightweight typing, DLQ tagging. |
| **Silver** | Business-ready canonical schema, deduplication, enrichment. |
| **Gold** | Curated aggregates and serving views/tables. |

Default sink is BigQuery native tables (SQL-first delivery). Use
BigLake/Iceberg only when interoperability is required by the data
product.

## Where to look next

- [docs/guides/dataflow.md](../../docs/guides/dataflow.md) — engineering standards.
- [docs/guides/error-handling.md](../../docs/guides/error-handling.md) — DLQ side outputs and replay.
- [docs/guides/observability.md](../../docs/guides/observability.md) — counters, freshness, SLO.
- [docs/guides/testing.md](../../docs/guides/testing.md) — Beam test patterns.
- [docs/blueprints/first-e2e-pipeline.md](../../docs/blueprints/first-e2e-pipeline.md) — end-to-end reference path.
- [docs/blueprints/step-3-private-runtime-checklist.md](../../docs/blueprints/step-3-private-runtime-checklist.md) — checklist for the first private runtime.
- [docs/diagrams/03-dataflow-shared.md](../../docs/diagrams/03-dataflow-shared.md) — reference diagram.
