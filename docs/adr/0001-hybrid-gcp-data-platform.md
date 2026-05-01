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
- **Layering pattern: Medallion (Bronze → Silver → Gold)** for data
  quality progression. Default for every new pipeline.

## Considered alternatives (layering)

These data-layer patterns were evaluated before settling on Medallion.
Each remains a valid choice for a runtime that has the constraints in
the "When to consider" column; we do not support them in this baseline
unless a future ADR explicitly opens the door.

| Pattern | Typical layers | When to consider | Why not the default here |
| :--- | :--- | :--- | :--- |
| **Medallion** (chosen) | Bronze → Silver → Gold | SQL + Lakehouse mix on GCP, simple ownership story | -- |
| **Curated / DW (Inmon, Kimball)** | Source → Staging → Curated → Mart | Enterprises with strong DW heritage, regulated industries that already use this vocabulary | Roughly equivalent to Silver + Gold combined; older naming, no operational gain over Medallion on a Lakehouse stack |
| **Data Vault 2.0** | Raw Vault (Hubs/Links/Sats) → Business Vault → Presentation | Heavy auditability, full historisation of source mutations, many heterogeneous sources that must be reconciled | Adds modelling overhead disproportionate to most pipelines we expect; would justify its own ADR + folder convention |
| **dbt-style** | Sources → Staging → Intermediate → Marts | Teams that already standardise on dbt for transforms | Near 1:1 with Medallion in semantics; choosing it would be a rename, not a new capability |
| **Diamond / Platinum extension** | Bronze → Silver → Gold → Diamond | Heavy ML feature pre-compute or executive-curated views beyond Gold | Not a published spec; if a pipeline needs a fourth layer, document it locally as a Gold sub-product |
| **Lambda Architecture** | Speed + Batch + Serving (orthogonal to Medallion) | Strict separation between low-latency views and batch-recomputed truth | Covered by [ADR 0002](0002-kappa-when-to-use.md) and [ADR 0004](0004-batch-streaming-operating-model.md): we run streaming and batch side by side without forcing Lambda's dual-pipeline rigidity |
| **Pure Kappa** | Single streaming path + replay | Workloads where the streaming logic genuinely covers backfill | Selective Kappa is allowed (see ADR 0002); pure Kappa is too restrictive for batch-heavy backfills |

## Consequences

- Documentation and code must separate patterns from services/tools.
- Pipeline design must be source/SLA driven, not ideology driven.
- Architecture claims should reflect implemented modules, not future goals.
