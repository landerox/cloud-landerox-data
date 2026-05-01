<!-- markdownlint-disable MD041 -->

## Summary

Describe the purpose of this PR.

## Type of Change

- [ ] Runtime placeholder/layout change (`functions/ingestion`, `functions/trigger`, or `dataflow/pipelines`)
- [ ] Bug fix
- [ ] Refactor
- [ ] CI/CD or tooling
- [ ] Documentation

## Scope

- Affected paths:
- Architecture impact (if any):
- New configuration or secrets required (if any):

## Validation

- [ ] `uv run pre-commit run --all-files`
- [ ] `uv run pytest`
- [ ] `uv run ruff check .` and `uv run ruff format --check .`
- [ ] `uv run pyright` (if Python logic changed)

## Checklist

- [ ] No hardcoded secrets or environment-specific IDs
- [ ] Tests added/updated for behavior changes
- [ ] Docs updated when architecture, contracts, or runbooks changed
- [ ] Backward-compatibility considered (or explicitly not required)

## Related Issues

Fixes #<issue-id> or `None`.
