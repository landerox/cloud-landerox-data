# Repository Guidelines

## Project Structure & Module Organization

- `functions/`: Cloud Functions code. Place runtime functions under `functions/ingestion/<name>/` or `functions/trigger/<name>/`; keep only folder placeholders in this public baseline repo.
- `dataflow/`: Apache Beam pipelines. Production pipelines go in `dataflow/pipelines/`; keep only folder placeholders in this public baseline repo.
- `shared/common/`: Infrastructure utilities only (`io.py`, `logging.py`, `secrets.py`). Do not add business transforms here.
- `tests/`: Mirrors source layout (`tests/functions/...`, `tests/dataflow/...`) plus shared fixtures in `tests/conftest.py`.
- `docs/`: Architecture, CI/CD, and engineering playbooks.

## Build, Test, and Development Commands

Use `just` wrappers (preferred):

- `just sync`: Install locked dependencies with `uv sync --frozen`.
- `just lint`: Run Ruff lint + formatting checks.
- `just type`: Run static typing with `ty`.
- `just test`: Run unit/integration tests with `pytest`.
- `just pre-commit-install`: Install local pre-commit hooks.

Direct equivalents when needed: `uv run pre-commit run --all-files`, `uv run pytest --cov=.`

## Coding Style & Naming Conventions

- Target runtime is Python 3.13.
- Indentation: 4 spaces for Python; 2 spaces for YAML/JSON/Markdown per `.editorconfig`.
- Ruff is the style authority (`line-length = 88`, double quotes, import sorting).
- `ty` rules are strict (`all = "error"`); add type hints for public functions and pipeline schemas.
- Naming: `snake_case` for modules/functions, `PascalCase` for classes, tests as `test_*.py`.
- Keep Cloud Function entrypoints in `main.py` (with `main()` where applicable).

## Testing Guidelines

- Framework: `pytest`; Beam code should use `apache_beam.testing.test_pipeline.TestPipeline`.
- Mock external GCP services (GCS, BigQuery, Secret Manager) in unit tests.
- Reuse fixtures in `tests/conftest.py` before adding new mocks.
- Mirror test paths to implementation paths.
  Example: `functions/ingestion/payments/webhook/main.py` -> `tests/functions/payments/webhook/test_main.py`.
- No minimum coverage threshold is enforced yet; include focused tests for every behavior change.

## Commit & Pull Request Guidelines

- Follow Conventional Commits (Commitizen enforced), e.g., `feat: add pubsub validator`, `fix: handle empty payload`.
- PRs should include: concise summary, change type, affected modules, and validation commands run.
- Before opening a PR, run: `uv run pre-commit run --all-files` and `uv run pytest`.
- For ingestion/function changes, avoid hardcoded table IDs, URLs, or bucket names; use config files and `shared.common.secrets`.
