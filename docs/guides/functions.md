# Cloud Functions Engineering Guide

This guide covers Cloud Functions used for ingestion and lightweight event-driven
tasks.

## 1) Scalable folder strategy (recommended)

Keep top-level split by role, then group by domain and source/event purpose:

```bash
functions/
├── ingestion/
│   └── <domain>/<source>_<mode>/
│       ├── main.py
│       ├── requirements.txt
│       ├── config.template.json
│       └── README.md
└── trigger/
    └── <domain>/<event>_<purpose>/
        ├── main.py
        ├── requirements.txt
        ├── config.template.json
        └── README.md
```

Conventions:

- Use `ingestion/` for API/webhook/pull entry points.
- Use `trigger/` for Pub/Sub, Storage, Scheduler, and Eventarc-driven handlers.
- Mirror tests in `tests/functions/<domain>/...`.

## 2) Function roles

- **Ingestion functions:** receive source data, validate contracts, and land/publish
  events.
- **Trigger functions:** react to events for post-processing, orchestration, or
  control-plane actions.

## 3) Diagram baseline (`1` or `2` diagrams)

- Use **one** Functions diagram when ingestion and trigger handlers are simple and
  tightly related.
- Use **two** diagrams when ingestion and trigger/orchestration are independent
  deploy/ownership units.

Reference templates:

- [Functions Shared](../diagrams/04-functions-shared.md)
- [Functions Ingestion HTTP/Webhook](../diagrams/04a-functions-ingestion-http.md)
- [Functions Trigger/Orchestration](../diagrams/04b-functions-trigger-orchestration.md)

## 4) Ingestion patterns

Choose pattern by source profile:

- **API -> Pub/Sub:** preferred for bursty traffic and retry resilience.
- **API -> GCS:** preferred for immutable archival and low-frequency sources.
- **API -> Pub/Sub + GCS:** use when both replayability and low-latency consumers
  are required.

## 5) Data and path conventions

- Required metadata: `event_id`, `event_time`, `source`, `schema_version`.
- Bronze path convention:
  `gs://<bucket>/<source>/dt=YYYY-MM-DD/format=<json|avro|parquet>/<file>`
- Timestamps must be UTC (RFC3339).

## 6) Reliability and security

- Keep handlers idempotent where possible.
- Use retries with bounded backoff for outbound HTTP calls.
- Never hardcode secrets, bucket names, table IDs, or project IDs.
- Read secrets via `shared.common.get_secret`.

## 7) CI/CD implications

For many functions, avoid all-in-one deploy jobs:

- Keep one shared CI workflow for quality gates.
- Deploy functions selectively by changed paths in `functions/**`.
- Prefer independent deploy units per function module folder.

## 8) Quality checks

```bash
just lint
just type
just test
```

For local HTTP function debugging:

```bash
uv run functions-framework --target=main --debug
```
