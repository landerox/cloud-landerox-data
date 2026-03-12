# First Runtime Scope (Step 2)

## Purpose

Define the first production scope before any runtime implementation. This document is intended for a **private runtime repository**, while `cloud-landerox-data` remains the public baseline.

## Selected scope (recommended)

- **Data product name:** `source_events_v1`
- **Source profile:** external webhook/API events (JSON)
- **Primary mode:** streaming (`Pub/Sub -> Dataflow`)
- **Fallback mode:** batch replay/backfill (`GCS -> Dataflow`)
- **Primary sink:** BigQuery native Silver table
- **Optional sink:** BigLake/Iceberg only if interoperability is required later

## Repository topology decision (recommended)

- **Runtime code location:** private runtime repo (not this public baseline).
- **Dataflow structure:** `dataflow/pipelines/<domain>/<layer>/<pipeline_name>/`.
- **Functions structure:** `functions/ingestion/<domain>/<source>_<mode>/` and
  `functions/trigger/<domain>/<event>_<purpose>/`.
- **CI/CD model:** shared CI + selective CD by changed module path.

## Contract v1

- Required fields:
  - `event_id` (string, stable idempotency key)
  - `event_time` (RFC3339 UTC)
  - `source` (string)
  - `schema_version` (string, start with `1.0`)
  - `payload` (object)
  - `ingested_at` (RFC3339 UTC)
- Compatibility policy:
  - Backward-compatible additions allowed
  - Breaking changes require version bump and migration runbook

## SLO and reliability targets

- End-to-end p95 latency (ingest to Silver): `<= 5 minutes`
- Error rate (invalid + processing failures): `< 1% daily`
- Freshness objective for Silver table: `<= 10 minutes`
- DLQ policy: route invalid records with reason codes, replay within 24h

## Governance baseline

- Classify dataset/table for PII sensitivity
- Define Bronze/DLQ/Silver retention windows
- Restrict IAM by dataset/table role boundaries

## Out of scope for first runtime

- Gold business aggregates
- CDC connectors
- Databricks/Delta interoperability
- Multi-team Data Mesh ownership model

## Exit criteria for Step 2

1. Scope approved (source profile, mode, sink, SLOs).
2. Contract v1 fields frozen.
3. Replay and backfill strategy agreed.
4. Security/governance baseline accepted.

After approval, Step 3 can implement this in a private runtime repo without exposing personal pipelines publicly.

Implementation guide: [Step 3: Private Runtime Implementation Checklist](step-3-private-runtime-checklist.md)
