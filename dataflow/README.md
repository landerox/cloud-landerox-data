# Dataflow Pipelines

This directory contains Apache Beam pipelines designed for the **Lakehouse (Silver Layer)**, following the **Unified Kappa Architecture**.

## Structure

- **`pipelines/`**: Production-ready pipelines organized by domain.
- **`examples/`**: Reference templates and best-practice samples.
  - **`gold_summary/`**: Example of aggregation towards the Gold layer.
  - **`template/`**: The "Golden Path" reference for a Kappa pipeline (Bronze to Silver/Iceberg).

## Development Standards

We use the [Astral](https://astral.sh/) ecosystem to ensure high performance and safety:

- **Type Safety:** All pipelines must use `typing.NamedTuple` for schemas. Validate locally using `uv run ty`.
- **Linting:** Enforced by `ruff`. No manual `pylint` or `pyright` comments should be added.
- **Unified Logic:** A single pipeline codebase **must** handle both **Streaming** (Pub/Sub) and **Batch** (GCS) modes. Splitting logic into separate batch and streaming pipelines is an anti-pattern; we prioritize identical code for real-time and historical processing.
- **Lakehouse First:** Silver layer outputs should choose the most efficient format via **BigLake**:
  - **Apache Iceberg:** For transactional datasets requiring ACID and Upserts.
  - **Standard Parquet/Avro:** For high-throughput immutable logs or Write-Truncate snapshots.

## Creating a New Pipeline

Each pipeline must follow this structure:

```bash
pipelines/my-pipeline/
├── pipeline.py        # Required: Main entry point
├── metadata.json      # Required: Flex Template parameters
├── requirements.txt   # Required: Managed via uv
├── transforms.py      # Optional: Modular DoFn classes
└── Dockerfile         # Required: Flex Template container definition
```

### Local Development & Quality Assurance

```bash
# 1. Setup environment
uv sync

# 2. Run Quality Checks
uv run ruff check .
uv run ty

# 3. Run with DirectRunner (Local)
uv run python pipeline.py \
  --runner=DirectRunner \
  --input_mode=batch \
  --input_path=gs://bucket/raw/file.json
```

## Flex Templates

Production pipelines are packaged as **Flex Templates**. This allows decoupling the execution environment from the CI/CD environment. For deployment details, see the [CI/CD Guide](../docs/cicd.md).
