# Shared Library (`common`)

This directory contains **infrastructure utilities only** -- NOT business logic.

## Purpose

Provide consistent, low-level utilities across all components to ensure
architectural alignment with the **GCP hybrid warehouse + lakehouse**
(BigQuery + BigLake/Iceberg) baseline.

## Modules

| Module | Purpose |
| :--- | :--- |
| `io.py` | Beam I/O factories: `KappaOptions`, `get_source` (Pub/Sub or GCS), `get_sink` (BigQuery via Storage Write API or File Loads). |
| `logging.py` | `CloudLoggingFormatter`, `setup_cloud_logging` (replaces handlers), `attach_cloud_logging_formatter` (non-destructive variant for Functions Framework / Dataflow workers), `trace_context`, and W3C `traceparent` helpers (`parse_traceparent`, `build_traceparent`, `current_traceparent`, `trace_context_from_traceparent`) for cross-service propagation into Cloud Logging. |
| `secrets.py` | `get_secret(secret_id, project_id=None)` with cached client and typed `SecretNotFoundError` on Google API failures. |
| `validation.py` | `validate_contract(data, contract_class)` raising `ContractValidationError` (with PII-safe error logs). |
| `exceptions.py` | Project exception hierarchy with stable `reason_code` strings: `CloudLanderoxError` (base) → `ConfigError` (`SecretNotFoundError`), `ContractError` (`ContractValidationError`, `SchemaIncompatibleError`), `PipelineIOError` (`SourceReadError`, `SinkWriteError`), `TransientError` (`ExternalServiceError`), `PermanentError` (`PoisonMessageError`). |
| `dlq.py` | Canonical `DLQPayload` plus `publish_to_pubsub_dlq`, `write_to_gcs_dlq`, `build_dlq_payload`, `load_dlq_payload` for replay tooling. |
| `retry.py` | `@retry` decorator with exponential backoff, full jitter, and injectable `sleeper`/`clock`/`rng` for deterministic tests. |
| `metrics.py` | `PipelineMetrics` with the canonical Beam counters (`records_processed`, `records_invalid`, `records_late`, `bytes_read`, `bytes_written`). |
| `tracing.py` | OpenTelemetry → Cloud Trace wiring: `setup_tracing` (installs a `TracerProvider` with `CloudTraceSpanExporter` + `BatchSpanProcessor`), `get_tracer`, and `start_span` (opens a span and binds its IDs to `trace_context` so logs and traces share the same correlation key). |

All public symbols are re-exported from `shared.common` via `__init__.py`.
See `tests/shared/common/test_package_exports.py` for the enforced surface.

## Architectural principles

### 1. Autonomous components

**Do NOT add business logic, transforms, or domain-specific code here.**

Each Cloud Function and Dataflow pipeline must be **fully self-contained**:

- Functions define their own parsing, contracts, and orchestration.
- Pipelines define their own DoFns and schemas (`NamedTuple` / Pydantic).
- This prevents cascading failures when modifying shared code.

### 2. Multi-format support

Utilities here are designed to support the Bronze multi-format strategy
(JSON, Avro, Parquet) so processing components can interact with the
lakehouse seamlessly.

### 3. Stable contracts

- Every exception has a class-level `reason_code` -- safe to use as a DLQ
  tag or dashboard filter. New codes go in a PR, never inline.
- DLQ payload shape is a Pydantic model (`DLQPayload`); replay tools
  import it directly to avoid drift.

## Usage

- **Cloud Functions:** the library is copied (or `pip install .`'d) into
  the function folder during CI/CD.
- **Dataflow:** the library is installed via `pip install .` during the
  Flex Template build process.

## Development standards

- **Type safety:** validated via `uv run pyright` (strict mode).
- **Linting:** enforced by `ruff`. No manual `# noqa` without a rule code
  and a justification comment.
- **Testing:** every public helper has a unit test under
  `tests/shared/common/`. Mocks (GCS, BigQuery, Secret Manager, Beam)
  live in `tests/conftest.py`.

See [docs/guides/coding-style.md](../docs/guides/coding-style.md),
[docs/guides/error-handling.md](../docs/guides/error-handling.md), and
[docs/guides/observability.md](../docs/guides/observability.md) for the
canonical rules.
