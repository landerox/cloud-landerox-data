# Dataflow Engineering Guide

This document outlines the best practices for developing Apache Beam pipelines, focusing on **Silver Layer (Lakehouse)** processing and **Apache Iceberg** interoperability.

## 1. Multi-Source Ingestion (Bronze to Silver)

Our Dataflow pipelines follow the **Unified Kappa Pattern**, ensuring that a single codebase handles both real-time and historical data.

### Ingestion Modes

- **Streaming:** Consumes from Pub/Sub (usually JSON/Avro payloads).
- **Batch:** Consumes from GCS (JSON, Avro, or Parquet).
- **API Pull (Batch):** For high-volume external data, the pipeline can act as a "Puller", connecting directly to REST/GraphQL APIs during the execution to download and process large datasets without an intermediate landing zone.

---

## 2. Silver Layer: Table Formats & Patterns

Choosing the right table format and write disposition is critical for performance and cost.

### Apache Iceberg (Transactional)

Use for datasets requiring **ACID consistency**, **Upserts/Merges**, or **Schema Evolution**.

- **Data Files:** Parquet (standardized).
- **Metadata:** Managed by Iceberg for time-travel and snapshotting.

### Standard BigLake (Non-Transactional)

Use for high-throughput or simple datasets using Parquet/Avro directly.

- **Append Pattern:** Ideal for immutable event streams or logs to avoid metadata overhead.
- **Write-Truncate Pattern:** Ideal for small-to-medium reference tables (Masters) where you replace the entire state daily.

---

## 3. Implementation Best Practices

### NamedTuples & Type Safety

Use `typing.NamedTuple` for all PCollections. This ensures that transformations (e.g., Avro Bronze to Parquet Silver) are type-safe and aligned with BigQuery/BigLake schemas.

### Sink Configuration

- **Transactional Sinks:** Configure `WriteDisposition.WRITE_APPEND` with Iceberg logic for incremental merges.
- **Standard Sinks:** Use `WRITE_TRUNCATE` for snapshotting and `WRITE_APPEND` for simple log ingestion.
- **File Management:** Prevent "Small File Problem" by using `GroupByKey` or Beam's file grouping features before the final write.

---

## 4. Quality Assurance & Standards

### Testing Cross-Format Logic

When writing unit tests with `TestPipeline`, include samples of different input formats (JSON vs Avro) to verify that your `DoFn` logic is truly format-agnostic.

```python
# Example: Testing a transform that handles both dicts (JSON) and Tuples (Avro)
def test_format_agnostic_transform(self):
    with TestPipeline() as p:
        # ... logic ...
```

### Astral Toolchain

- **Dependency Management:** All pipelines use `uv` for environment isolation.
- **Linter:** `ruff` ensures consistent code style across all pipeline components.
