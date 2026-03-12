# Shared Library (`common`)

This directory contains **infrastructure utilities only** - NOT business logic.

## Purpose

Provide consistent, low-level utilities across all components to ensure architectural alignment with the **GCP Lakehouse (BigLake + Iceberg/Standard)**:

- **I/O Abstraction (`io.py`):** Unified access to GCS and BigQuery, supporting both Streaming (Kappa) and Batch modes.
- **Logging (`logging.py`):** Standardized JSON structure for Cloud Logging with structured metadata.
- **Secrets (`secrets.py`):** Secure access to GCP Secret Manager.

## Architectural Principles

### 1. Autonomous Components

**Do NOT add business logic, transforms, or domain-specific code here.**

Each Cloud Function and Dataflow pipeline must be **fully self-contained**:

- Functions define their own parsing and validation.
- Pipelines define their own DoFns and schemas (`NamedTuples`).
- This prevents cascading failures when modifying shared code.

### 2. Multi-Format Support

Utilities in `common` are designed to support the **Bronze Multi-format strategy** (JSON, Avro, Parquet), ensuring that processing components can interact with the Lakehouse seamlessly.

## Usage

- **Cloud Functions:** Library is copied into the function folder during CI/CD.
- **Dataflow:** Library is installed via `pip install .` during the Flex Template build process.

## Development Standards (Astral)

- **Type Safety:** Validated via `uv run ty`.
- **Linting:** Enforced by `ruff`. No manual linting comments should be used.
