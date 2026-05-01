# Function Tests

Placeholder mirroring `functions/`.

## Status

This folder is **intentionally empty in this public baseline.** Tests
for production functions live alongside the runtime code in private
runtime repositories.

## Layout

Mirror the runtime source tree exactly:

```text
functions/ingestion/<domain>/<source>_<mode>/main.py
  -> tests/functions/<domain>/<source>_<mode>/test_main.py

functions/trigger/<domain>/<event>_<purpose>/main.py
  -> tests/functions/<domain>/<event>_<purpose>/test_main.py
```

## Standards

- Default marker is `unit`. Mock GCP, HTTP, and time. See
  [docs/guides/testing.md §1](../../docs/guides/testing.md#1-test-categories).
- Reuse fixtures from [`tests/conftest.py`](../conftest.py)
  (`mock_http_request`, `mock_cloud_event`, `mock_storage_client`,
  `mock_secret_manager`, etc.) before adding new ones.
- Cover happy path, contract violation, DLQ routing, and credential-missing
  failure modes per [docs/guides/testing.md §9](../../docs/guides/testing.md#9-what-to-test).

## Where to look next

- [tests/README.md](../README.md) — fixtures and run commands.
- [docs/guides/testing.md](../../docs/guides/testing.md) — test categories and quality bars.
- [functions/ingestion/README.md](../../functions/ingestion/README.md) — runtime layout.
- [functions/trigger/README.md](../../functions/trigger/README.md) — runtime layout.
