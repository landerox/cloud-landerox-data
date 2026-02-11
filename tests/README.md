# Tests

This directory mirrors the source structure for Unit and Integration tests.

## Structure

* `functions/`: Tests for Cloud Functions (using `unittest.mock` and `functions-framework`).
* `dataflow/`: Tests for Beam pipelines (using `TestPipeline`).
* `conftest.py`: Shared Pytest fixtures (GCS, BigQuery, Secrets mocks).

## Running Tests

We use `pytest` powered by `uv` for fast execution.

```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/functions/examples/ingestion_template/test_main.py

# Run with coverage
uv run pytest --cov=.
```

## Testing Standards

* **Unit Tests:** Must mock all external GCP services (GCS, BQ, Secret Manager).
* **Dataflow Tests:** Use `apache_beam.testing.test_pipeline.TestPipeline` to verify `DoFn` logic locally.
* **Fixtures:** Use the shared fixtures in `conftest.py` instead of creating new mocks for every test.
