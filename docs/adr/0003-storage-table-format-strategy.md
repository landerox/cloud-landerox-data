# ADR 0003: Storage and Table Format Strategy

- Status: Accepted
- Date: 2026-03-05

## Context

Data products require both high-speed SQL delivery and open-format interoperability. Different datasets also have different mutation patterns (append-only vs upsert/snapshot).

## Decision

- Bronze: JSON/NDJSON, Avro, or Parquet on GCS; optional raw landing in BigQuery.
- Silver/Gold default: BigQuery native tables for warehouse-first workloads.
- Silver optional: BigLake external tables over Parquet/Avro or Iceberg where interoperability and table-level semantics are needed.
- Delta/Hudi are not primary targets in this repo, but interoperability can be considered case by case.

## Consequences

- Format choice is workload-driven, not fixed globally.
- Module docs must declare: file format, table format, and write pattern (`append`, `truncate`, `merge/upsert`).
- Tests should validate schema compatibility across selected formats.
