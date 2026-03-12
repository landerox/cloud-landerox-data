# ADR 0004: Batch + Streaming Operating Model

- Status: Accepted
- Date: 2026-03-05

## Context

The platform receives sources with mixed latency, volume, and reliability profiles. A single ingestion mode cannot optimize all workloads.

## Decision

Adopt dual operating modes:

- Streaming for low-latency event ingestion and near-real-time transformations.
- Batch for scheduled extraction, historical backfills, and cost-controlled processing.

Both modes are supported by shared contracts and observability standards.

## Consequences

- Every new data product should explicitly state its primary mode and fallback mode.
- Replay and reprocessing procedures must be documented.
- SLAs and cost targets should be defined per pipeline, not globally.
