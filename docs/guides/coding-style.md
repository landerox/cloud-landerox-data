# Coding Style Guide

Canonical source of coding style for this repository. Covers Python,
naming, imports, type hints, docstrings, SQL, and configuration.

## Source of truth

`pyproject.toml` is the **enforced** configuration: if a rule in this
guide drifts from what `ruff` / `pyright` / `pytest-cov` enforce, the
configuration wins and the guide must be updated to match.

## Tooling at a glance

- Formatter: `ruff format` (88 cols, double quotes).
- Linter: `ruff check` with the rule families listed in [§3](#3-linting).
- Type checker: `pyright` in `strict` mode (suppresses only
  `reportUnknown*` for third-party libs without stubs).
- Pre-commit: `uv run pre-commit run --all-files` mirrors CI.
- Local quality gate: `just check` (lint + type + test + audit).

## Companion guides

- [Testing standards](testing.md) — markers, mocking policy, coverage gate.
- [Error handling](error-handling.md) — exception hierarchy, retry, DLQ.
- [Observability](observability.md) — structured logging, trace context,
  canonical metrics.
- [Security (developer)](security.md) — secrets, SQL params, PII,
  dependencies.

## 1) Python version

- Target: **Python 3.13** only (`requires-python = ">=3.13,<3.14"`).
- Ruff `target-version = "py313"`.
- Prefer modern syntax: PEP 695 generics, `X | Y` unions,
  `from __future__ import annotations` is **not** required.

## 2) Formatting

- Formatter: **`ruff format`** (no black, no autopep8).
- **Line length: 88** (Ruff default). Enforced by `ruff format`.
- Quote style: **double quotes**.
- Trailing commas are added automatically where Ruff emits them.
- Docstring code blocks are formatted (`docstring-code-format = true`).

Run:

```bash
just format
```

## 3) Linting

- Linter: **`ruff check`** with these rule families enabled:
  `E`, `W`, `F`, `I`, `B`, `C4`, `UP`, `ARG`, `SIM`, `PTH`, `ERA`, `PL`, `RUF`.
- Ignored rules (documented rationale):
  - `E501` — line length handled by the formatter.
  - `PLR0913` — argument count limit not useful for Beam/factory signatures.
  - `PLR2004` — magic values are acceptable for now.
- Per-file ignores apply only to `tests/**/*.py` (see `pyproject.toml`).

Never suppress a rule with inline `# noqa` unless the rule ID is written
explicitly (`# noqa: RUF001`) and a short comment explains why.

## 4) Type hints

- **Every function and method must have type hints** on parameters and return.
- Type checker: **`pyright`** in `strict` mode (`[tool.pyright]` in `pyproject.toml`). The same engine powers VS Code Pylance, so the editor and CI report identical findings.
- Use PEP 695 syntax for generics:

  ```python
  def validate_contract[T: BaseModel](data: dict, contract: type[T]) -> T | None: ...
  ```

- Prefer `X | None` over `Optional[X]`; `list[int]` over `List[int]`.
- `Any` is a smell — justify it with a comment when unavoidable
  (e.g. Beam / Pydantic dynamic payloads).
- Do not leave `# type: ignore` without a rule code and reason.

## 5) Docstrings

- Style: **Google**.
- Required on every **public** symbol (module, class, function). Private
  helpers (prefixed with `_`) may omit docstrings when behaviour is obvious.
- First line: imperative, under 80 chars, ending in a period.
- Sections in order when applicable: `Args`, `Returns`, `Raises`, `Example`.

Template:

```python
def get_secret(secret_id: str, project_id: str | None = None) -> str:
    """Retrieve a secret value from GCP Secret Manager.

    Args:
        secret_id: ID of the secret to retrieve.
        project_id: GCP project ID. Defaults to ``GOOGLE_CLOUD_PROJECT``.

    Returns:
        The latest version of the secret as a string.

    Raises:
        SecretNotFoundError: If the project or secret cannot be resolved.
    """
```

## 6) Imports

- Sorted and grouped by `ruff`'s isort (`force-sort-within-sections = true`).
- Group order: stdlib, third-party, first-party, local. Blank line between
  groups is inserted by the formatter.
- Avoid wildcard imports (`from x import *`).
- Re-exports from packages go in `__init__.py` via explicit `__all__`.

## 7) Naming conventions

| Kind | Convention | Example |
| :--- | :--- | :--- |
| Modules, packages, functions, variables | `snake_case` | `get_sink`, `kappa_options` |
| Classes, exceptions, type aliases | `PascalCase` | `KappaOptions`, `CloudLanderoxError` |
| Constants | `UPPER_SNAKE_CASE` | `DEFAULT_TIMEOUT_SECONDS` |
| Private helpers | leading `_` | `_build_client` |
| Test modules, test functions | `test_*` | `test_get_secret.py`, `test_returns_none` |
| Function folders | `<source>_<mode>` | `payments_webhook`, `gcs_finalize_notify` |
| Pipeline folders | `<entity>_<layer>_<mode>` | `orders_silver_batch` |

## 8) Data validation

- External payloads (HTTP, Pub/Sub, GCS) must be validated with **Pydantic v2**
  models via `shared.common.validate_contract`.
- Model classes are the **contract surface** — keep them in each module's
  `contracts.py` (functions) or `schemas.py` (pipelines), not in
  `shared/common/`.
- Prefer `model_validate` over `__init__` when Pydantic v2 behaviour matters.

## 9) Logging inside code

See [observability.md](observability.md) for the full policy. The two
rules that apply everywhere:

- Use the stdlib `logging` module, not `print`.
- Do not pre-format messages with f-strings; pass args:
  `logging.info("reading %s", path)`.
- Attach structured context via `extra={"extra_fields": {...}}` so
  `CloudLoggingFormatter` can emit it as JSON.

## 10) Error handling

See [error-handling.md](error-handling.md) for the full policy. Two rules
that apply everywhere:

- Never use a bare `except:` or `except Exception:` without re-raising or
  logging with context.
- Prefer raising a typed exception from the project hierarchy over returning
  `None` to signal failure in new code.

## 11) SQL

- Keywords in `UPPERCASE`, identifiers in `snake_case`.
- **Parameterized queries only.** String-formatted SQL is forbidden, even
  for "internal" constants.
- Qualify table references as `` `project.dataset.table` `` in BigQuery.

## 12) Configuration

- No hardcoded project IDs, bucket names, table IDs, region names, or
  endpoints. Read them from environment, `config.json`, or Secret Manager.
- `config.template.json` is committed; `config.json` is gitignored.

## 13) Comments

- Prefer self-explanatory code over comments.
- Write a comment only when the *why* is not obvious from the code
  (non-obvious constraint, workaround, intentional trade-off).
- Do not leave `TODO` without an owner and a tracking reference.

## Related

- [AGENTS.md](../../AGENTS.md)
- [testing.md](testing.md)
- [error-handling.md](error-handling.md)
- [`.github/CONTRIBUTING.md`](../../.github/CONTRIBUTING.md)
