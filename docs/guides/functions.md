# Cloud Functions Engineering Guide

This document outlines best practices for developing Cloud Functions, focused on the **Bronze Layer** (Multi-format Ingestion).

## 1. Multi-Format Ingestion Strategy

In a modern Lakehouse, choosing the right format in the Bronze layer is critical for downstream efficiency.

### Choosing the Right Format

| Format | Use Case | Rationale |
| :--- | :--- | :--- |
| **JSON (NDJSON)** | Webhooks, REST APIs | Best for flexible, changing schemas. |
| **Avro** | Database replication, CDC | Preserves strict schemas and complex data types. |
| **Parquet** | Structured bulk data | Smallest storage footprint and fastest BQ load times. |

### Path Convention (Hive-style)

Always use Hive-partitioned paths to enable automatic partition discovery in BigQuery/BigLake:
`gs://{bucket}/{source_name}/dt=YYYY-MM-DD/format={json|avro|parquet}/{file}`

---

## 2. Standard Architecture Patterns

### Pattern A: API -> GCS (Raw Landing)

- **Objective:** Land data in GCS as fast as possible for archival.
- **Implementation:** Save as NDJSON, Avro, or Parquet for long-term storage.

### Pattern B: API -> Pub/Sub (Async Decoupling)

- **Objective:** High availability and resilience for mission-critical webhooks.
- **Implementation:** The function only validates the payload and publishes to a Pub/Sub topic.
- **Downstream:** Use a **Pub/Sub to BigQuery Subscription** for zero-code ingestion into the Bronze Raw Dataset.

### Pattern C: Post-Processing (GCS Event Trigger)

- **Objective:** Perform lightweight tasks immediately after a file lands in Bronze.
- **Trigger:** `google.storage.object.finalize`.
- **Use Cases:** Metadata extraction, basic integrity checks, or notifying external systems (e.g., triggering a Dataflow job or a Dataform execution).

---

## 3. Performance & Resource Tips

- **Pub/Sub over HTTP:** Prefer Pattern B for high-concurrency APIs to avoid timeout issues.
- **Streaming Uploads:** For large API responses, stream the data directly to GCS.

---

## 4. Development Standards

- **Type Safety:** Use `ty` to validate that your API parsers match the expected schemas.
- **Quality:** Code must pass `uv run ruff check .`.
- **Secrets:** Access API keys via `shared.common.get_secret`.
