# ADR 0001: Hybrid GCP Data Platform

- Status: Accepted
- Date: 2026-03-05

## Context

The project needs to support multiple source profiles (API/webhooks, event streams, scheduled extracts) with different latency and interoperability requirements. A single-pattern architecture would overfit some workloads and under-serve others.

## Decision

Adopt a hybrid architecture:

- Warehouse-first path on BigQuery native tables for SQL-first analytics.
- Lakehouse path on GCS + BigLake for open-format interoperability.
- Batch and streaming as first-class modes.

## Consequences

- Documentation and code must separate patterns from services/tools.
- Pipeline design must be source/SLA driven, not ideology driven.
- Architecture claims should reflect implemented modules, not future goals.
