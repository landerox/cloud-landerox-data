# First End-to-End Pipeline Blueprint

## Goal

Define a credible runtime reference path for implementation in a **private runtime
repository**, while this repository remains a public baseline for architecture and
patterns.

## Proposed path

`Source API/Webhook -> Cloud Function (ingestion) -> Bronze (GCS + optional Pub/Sub) -> Dataflow -> Silver (BigQuery and/or BigLake) -> Gold (BigQuery)`

## Diagram references

- Context and E2E: [Diagram Catalog](../diagrams/README.md)
- Dataflow view (`1` or `2`): [03-dataflow-shared.md](../diagrams/03-dataflow-shared.md)
- Functions view (`1` or `2`): [04-functions-shared.md](../diagrams/04-functions-shared.md)

## Runtime module targets

- `functions/ingestion/<domain>/<source>_webhook/main.py`
- `functions/trigger/<domain>/gcs_finalize_<purpose>/main.py` (optional)
- `dataflow/pipelines/<domain>/silver/<data_product>/pipeline.py`
- `tests/functions/<domain>/...`
- `tests/dataflow/<domain>/...`

For larger runtimes, keep the same domain-first pattern across Bronze/Silver/Gold:

- `dataflow/pipelines/<domain>/bronze/<pipeline_name>/...`
- `dataflow/pipelines/<domain>/silver/<pipeline_name>/...`
- `dataflow/pipelines/<domain>/gold/<pipeline_name>/...`

## Data contract (minimum)

- Required fields: `event_id`, `event_time`, `source`, `payload`, `ingested_at`.
- Timestamp standard: RFC3339 UTC.
- Contract version field: `schema_version`.
- Compatibility policy: backward-compatible evolution by default.
- Invalid payload handling: route to DLQ with reason code.

## Write strategy

- Bronze archive: immutable files in `gs://<bucket>/<source>/dt=YYYY-MM-DD/...`
- Silver: start with BigQuery native table (`WRITE_APPEND`), then evaluate BigLake/Iceberg only if needed.
- Gold: aggregate table/materialized view in BigQuery.

## Observability and reliability

- Structured JSON logs in all components.
- Beam metrics for processed/error counters.
- Retry policy for external API calls.
- Idempotency key strategy based on `event_id` + source metadata.
- Deduplication policy (window or merge key) documented per sink.
- Freshness and latency SLOs defined per pipeline.

## Orchestration and replay

- Batch scheduling: Cloud Scheduler (or Workflows) for periodic runs.
- Replay runbook: DLQ replay job for scoped failures.
- Backfill runbook: full reprocessing path for systemic failures.

## Data quality and governance

- Bronze -> Silver quality checks (required fields, type checks, timestamp validity).
- Silver -> Gold quality checks (uniqueness, null thresholds, business constraints).
- Governance baseline:
  - PII classification tag per dataset/table.
  - Retention rules for Bronze, DLQ, and Silver/Gold.
  - IAM access boundaries by dataset/table.

## Minimum acceptance criteria

1. Ingestion function validates payload and persists/publishes successfully.
2. Dataflow pipeline runs in DirectRunner and transforms sample records end-to-end.
3. Unit tests cover success path, invalid payload path, and sink write behavior.
4. CI passes (`pre-commit`, `pytest`).
5. Module README documents mode (`stream` or `batch`), schema, and deployment parameters.
6. Replay/backfill runbooks exist and are executable.
7. SLO metrics and DQ checks are documented and testable.
