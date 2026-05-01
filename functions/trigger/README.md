# Trigger Functions

Placeholder for event-driven handlers (Pub/Sub, GCS, Scheduler, Eventarc).

## Status

This folder is **intentionally empty in this public baseline.** Production
trigger functions live in private runtime repositories. The folder is
kept so the layout, CI, and tooling are wired exactly the way runtime
modules will land.

## What goes here

One folder per deployable function:

```text
trigger/
└── <domain>/
    └── <event>_<purpose>/
        ├── main.py              # entrypoint with `main(event, context)` (CloudEvent)
        ├── contracts.py         # Pydantic v2 models for the event envelope
        ├── requirements.txt     # function-scoped runtime deps
        ├── config.template.json # runtime config (gitignored copy: config.json)
        └── README.md            # SLO, deploy params, runbook links
```

`<event>_<purpose>` is the canonical naming for a trigger folder
(e.g. `gcs_finalize_notify`, `pubsub_orders_dispatch`,
`scheduler_replay_dlq`). See
[coding-style.md §7](../../docs/guides/coding-style.md#7-naming-conventions).

## Required wiring

Every trigger function must:

- Validate the inbound CloudEvent payload via
  `shared.common.validate_contract(payload, ContractV1)`.
- Read secrets via `shared.common.get_secret`.
- Initialize structured logging via `shared.common.setup_cloud_logging`
  (see the caveat in that function's docstring before calling it from
  Functions Framework).
- Open a `shared.common.trace_context` from the inbound `traceparent`
  attribute when present so the chain stays correlated.
- Be **idempotent** under at-least-once delivery. Use the source's
  natural `event_id` (or a deterministic hash) as the dedup key.
- Route `ContractError` / `PermanentError` to a domain DLQ via
  `shared.common.publish_to_pubsub_dlq`.
- Mirror tests under `tests/functions/<domain>/<event>_<purpose>/test_main.py`.

## Where to look next

- [docs/guides/functions.md](../../docs/guides/functions.md) — engineering standards.
- [docs/guides/error-handling.md](../../docs/guides/error-handling.md) — idempotency, DLQ, retry.
- [docs/guides/observability.md](../../docs/guides/observability.md) — log fields and trace.
- [docs/blueprints/first-e2e-pipeline.md](../../docs/blueprints/first-e2e-pipeline.md) — end-to-end reference path.
- [docs/blueprints/step-3-private-runtime-checklist.md](../../docs/blueprints/step-3-private-runtime-checklist.md) — checklist for the first private runtime.
- [docs/diagrams/04b-functions-trigger-orchestration.md](../../docs/diagrams/04b-functions-trigger-orchestration.md) — reference diagram.
