# Cloud Functions

This directory contains lightweight, event-driven serverless functions (Gen 2) designed for the **Bronze Layer (Ingestion)**.

## Structure

- **`ingestion/`**: Functions that pull data from external APIs or sources.
- **`trigger/`**: Functions that react to events (e.g., GCS arrival, Pub/Sub messages).
- **`examples/`**: Reference templates for new functions.

## Bronze Ingestion & Processing Patterns

We follow three primary serverless patterns for the Bronze layer:

### Pattern A: API -> GCS (Archival)

Directly persists raw payloads into Cloud Storage. Ideal for immutable auditing and low-cost archival.

### Pattern B: API -> Pub/Sub (Async Decoupling)

Standard for mission-critical webhooks. The function only validates and publishes to Pub/Sub, ensuring high availability and backpressure management via downstream BigQuery Subscriptions.

### Pattern C: GCS Event -> CF (Post-Processing)

Triggered by `google.storage.object.finalize`. Performs lightweight tasks like file validation or triggering the next stage in the Lakehouse (Dataflow/Dataform).

---

## Bronze Ingestion Strategy (Multi-Format)

Our functions must land data in the most efficient format for the source, following Hive-style partitioning to enable automatic discovery by BigLake/BigQuery.

### Format Selection

| Format | Best For | Implementation Tip |
| :--- | :--- | :--- |
| **JSON** | Flexible/Dynamic APIs | Use standard `json` with NDJSON format. |
| **Avro** | Database replication | Use `fastavro` for schema preservation. |
| **Parquet** | Structured bulk data | Use `pyarrow` if memory allows (>512Mi). |

### Partitioning Convention

`gs://{bucket}/{source_name}/dt=YYYY-MM-DD/format={json|avro|parquet}/{file}`

## Creating a New Function

```bash
{ingestion|trigger}/my-function/
├── main.py              # Required: Entry point with main()
├── requirements.txt     # Required: Managed via uv
├── config.template.json # Required: Example configuration
└── deploy.json          # Required: Deployment settings
```

## Development Standards (Astral)

- **Type Safety:** Use Python 3.12 type hints and `typing.NamedTuple`. Validate locally with `uv run ty`.
- **Linting:** Enforced by `ruff`. Avoid `pylint` or `pyright` comments.
- **Resilience:** Use the `tenacity` library for external API retries.
- **Secrets:** Access credentials via `shared.common.get_secret`.

## Local Testing

```bash
# Install framework
uv pip install functions-framework

# Run locally
functions-framework --target=main --debug
```

## Deployment

Functions are automatically deployed when pushed to `main`. See [CI/CD Guide](../docs/cicd.md).
