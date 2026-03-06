# Contributing Guide

Thanks for contributing.

## Quick start

### Prerequisites

- Python 3.13+
- `uv`
- `just`

### Setup

```bash
just sync
just pre-commit-install
just test
```

## Development workflow

1. Create a branch: `git checkout -b feat/<short-name>`.
2. Implement changes in the appropriate module.
3. Run quality checks:
   - `just lint`
   - `just type`
   - `just test`
4. Auto-fix formatting issues: `just format`.
5. Commit with Conventional Commits (`feat:`, `fix:`, `docs:`, `chore:`).
6. Open a PR using the PR template.

## Adding a new Cloud Function

Follow the folder strategy in [Cloud Functions Guide](../docs/guides/functions.md):

```text
functions/
  ingestion/<domain>/<source>_<mode>/
    main.py
    requirements.txt
    config.template.json
    README.md
```

Or for trigger functions:

```text
functions/
  trigger/<domain>/<event>_<purpose>/
    main.py
    requirements.txt
    config.template.json
    README.md
```

Mirror tests at:

```text
tests/functions/<domain>/<source_or_event>/test_main.py
```

Use `shared.common.get_secret` for credentials and `shared.common.setup_cloud_logging` for logging. Keep the entrypoint in `main.py` with a `main()` function.

## Adding a new Dataflow pipeline

Follow the folder strategy in [Dataflow Guide](../docs/guides/dataflow.md):

```text
dataflow/pipelines/
  <domain>/
    bronze/<pipeline_name>/
      pipeline.py
      metadata.json
      requirements.txt
      README.md
    silver/<pipeline_name>/
    gold/<pipeline_name>/
```

Mirror tests at:

```text
tests/dataflow/<domain>/<layer>/<pipeline_name>/test_pipeline.py
```

Use `shared.common.KappaOptions`, `get_source()`, and `get_sink()` for I/O. Use typed schemas (`typing.NamedTuple` or Pydantic models). Use `shared.common.validate_contract` for input validation.

## Naming conventions

- Modules/functions: `snake_case`
- Classes: `PascalCase`
- Test files: `test_*.py`
- Function folders: `<source>_<mode>` (e.g., `payments_webhook`, `gcs_finalize_notify`)
- Pipeline folders: `<entity>_<layer>_<mode>` (e.g., `orders_silver_batch`)

## Starter templates

Copy and adapt the baseline templates from `docs/blueprints/templates/`:

- `contracts/source_events_v1.schema.json` -- data contract template
- `config/config.template.json` -- runtime configuration template

See the full handoff checklist at [Step 3 Private Runtime Checklist](../docs/blueprints/step-3-private-runtime-checklist.md).

## Project state reminder

This repository is a public baseline for architecture, structure, and standards.

- Runtime folders (`functions/ingestion`, `functions/trigger`, `dataflow/pipelines`) are placeholders by design in this public baseline.
- CI quality checks are active.
- Deployment workflows are planned but not yet active in this repository.
- It is valid to keep production runtime modules in private repositories.

## Security and config

- Do not hardcode secrets, bucket names, table IDs, or endpoint credentials.
- Use environment configuration and `shared.common.secrets`.
- For security reporting, see [SECURITY.md](SECURITY.md).
