# Tests

This directory provides baseline tests for repository structure and shared test
fixtures.

## Structure

* `functions/`: Placeholder folder for function tests in private runtime repos.
* `dataflow/`: Placeholder folder for pipeline tests in private runtime repos.
* `test_repository_layout.py`: Validates expected baseline folder structure.
* `conftest.py`: Shared fixtures for GCS, BigQuery, and Secret Manager mocks.

## Running Tests

We use `pytest` powered by `uv` for fast execution.

```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/test_repository_layout.py

# Run with coverage
uv run pytest --cov=.
```

## Testing Standards

* **Runtime Unit Tests:** Must mock external GCP services (GCS, BQ, Secret Manager).
* **Dataflow Runtime Tests:** Use `apache_beam.testing.test_pipeline.TestPipeline`.
* **Fixtures:** Reuse `tests/conftest.py` before adding new mocks.
