# Dataflow Engineering Guide

This guide defines practical standards for Apache Beam pipelines in this repo.

## 1) Scalable folder strategy (recommended for ~50 pipelines)

Use **domain first, then Medallion layer**:

```bash
dataflow/pipelines/
└── <domain>/
    ├── bronze/
    │   └── <pipeline_name>/
    │       ├── pipeline.py
    │       ├── metadata.json
    │       ├── requirements.txt
    │       └── README.md
    ├── silver/
    │   └── <pipeline_name>/
    └── gold/
        └── <pipeline_name>/
```

Conventions:

- One deployable pipeline per module folder.
- Keep names explicit: `<source>_bronze_stream`, `<entity>_silver_batch`,
  `<mart>_gold`.
- Mirror tests by domain and layer:
  `tests/dataflow/<domain>/<layer>/<pipeline_name>/test_pipeline.py`.

This avoids a flat folder with dozens of pipelines and keeps ownership boundaries
clear.

## 2) Layer responsibilities

- **Bronze:** ingestion normalization, contract checks, lightweight typing, DLQ tags.
- **Silver:** business-ready canonical schema, deduplication, enrichment.
- **Gold:** curated aggregates and serving views/tables for analytics consumption.

## 3) Operating modes

Use mode per source SLA and recovery needs:

- **Streaming mode:** Pub/Sub input for low-latency workloads.
- **Batch mode:** GCS/source pull for scheduled loads and backfills.
- **Single code path (Kappa-style):** preferred when stream and batch logic can be
  shared safely.
- **Split paths (Lambda-lite):** acceptable when constraints differ materially.

## 4) Diagram baseline (`1` or `2` diagrams)

- Use **one** Dataflow diagram when streaming and batch/replay share most
  transforms.
- Use **two** diagrams when stream and batch/replay differ materially in
  windowing, dedup, or sink behavior.

Reference templates:

- [Dataflow Shared](../diagrams/03-dataflow-shared.md)
- [Dataflow Streaming](../diagrams/03a-dataflow-streaming.md)
- [Dataflow Batch/Replay](../diagrams/03b-dataflow-batch-replay.md)

## 5) Storage targets

- Default Silver target: **BigQuery native tables** for SQL-first delivery.
- Optional Silver target: **BigLake external tables** on Parquet/Avro or Iceberg
  when interoperability is required.
- Choose write pattern explicitly: `WRITE_APPEND`, `WRITE_TRUNCATE`, or merge/upsert.

## 6) Implementation standards

- Use typed schemas (`typing.NamedTuple` or equivalent typed models).
- Keep infrastructure utilities in `shared/common`; keep domain transforms in each
  pipeline module.
- Add Beam metrics (`processed`, `errors`, `late_records`) and DLQ handling.
- Avoid implicit assumptions in transforms (timezone, schema version, null handling).

## 7) CI/CD implications

For large pipeline sets, avoid a single deploy job for all pipelines:

- Keep one shared CI workflow for quality gates.
- Deploy Dataflow modules selectively by changed paths in
  `dataflow/pipelines/**`.
- Build/version templates per pipeline module for rollback safety.

## 8) Quality checks

Run before PR:

```bash
just lint
just type
just test
```

For pipeline-focused local runs:

```bash
uv run python dataflow/pipelines/<domain>/<layer>/<pipeline_name>/pipeline.py \
  --runner=DirectRunner \
  --input_mode=batch \
  --input_path=tests/data/sample.json \
  --output_table=<project>:<dataset>.<table>
```

## 9) Testing requirements

- Unit-test transform logic with `apache_beam.testing.test_pipeline.TestPipeline`.
- Include parsing, contract validation, and DLQ path tests.
- Validate sink schema compatibility and write mode behavior.
