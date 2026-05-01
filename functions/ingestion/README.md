# Ingestion Functions

Placeholder for HTTP / API / webhook ingestion handlers.

## Status

This folder is **intentionally empty in this public baseline.** Production
ingestion functions live in private runtime repositories. The folder is
kept so the layout, CI, and tooling are wired exactly the way runtime
modules will land.

## What goes here

One folder per deployable function:

```text
ingestion/
└── <domain>/
    └── <source>_<mode>/
        ├── main.py              # entrypoint with `main(request)` (HTTP)
        ├── contracts.py         # Pydantic v2 models for inbound payloads
        ├── requirements.txt     # function-scoped runtime deps
        ├── config.template.json # runtime config (gitignored copy: config.json)
        └── README.md            # SLO, deploy params, runbook links
```

`<source>_<mode>` is the canonical naming for an ingestion folder
(e.g. `payments_webhook`, `orders_pull_batch`). See
[coding-style.md §7](../../docs/guides/coding-style.md#7-naming-conventions).

## Required wiring

Every ingestion function must:

- Validate the inbound payload via
  `shared.common.validate_contract(payload, ContractV1)`.
- Read secrets via `shared.common.get_secret`.
- Initialize structured logging via `shared.common.setup_cloud_logging`
  (see the caveat in that function's docstring before calling it from
  Functions Framework).
- Open a `shared.common.trace_context` for the request scope so logs
  stitch in Cloud Logging.
- Route `ContractError` / `PermanentError` to a domain DLQ via
  `shared.common.publish_to_pubsub_dlq` with the canonical
  `DLQPayload`.
- Mirror tests under `tests/functions/<domain>/<source>_<mode>/test_main.py`.

## Where to look next

- [docs/guides/functions.md](../../docs/guides/functions.md) — engineering standards.
- [docs/guides/error-handling.md](../../docs/guides/error-handling.md) — DLQ and retry policy.
- [docs/guides/observability.md](../../docs/guides/observability.md) — log fields and trace.
- [docs/guides/security.md](../../docs/guides/security.md) — secrets, IAM, PII.
- [docs/blueprints/first-e2e-pipeline.md](../../docs/blueprints/first-e2e-pipeline.md) — end-to-end reference path.
- [docs/blueprints/step-3-private-runtime-checklist.md](../../docs/blueprints/step-3-private-runtime-checklist.md) — checklist for the first private runtime.
- [docs/blueprints/templates/](../../docs/blueprints/templates/) — config + contract starter templates.
