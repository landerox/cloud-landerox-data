# Cloud Functions

This directory contains Cloud Functions used for ingestion and event-triggered post-processing.

## Current state

- `ingestion/` and `trigger/` are placeholders for runtime modules.
- Runtime function implementations are intentionally kept outside this public baseline.

## Directory layout (recommended at scale)

- `ingestion/`: HTTP/API pull functions and webhook handlers.
- `trigger/`: Event-driven handlers (Pub/Sub, GCS, Scheduler, Eventarc).

Suggested structure for private runtime repos:

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

## Supported ingestion patterns

- API/Event -> Pub/Sub (resilience and decoupling)
- API/Event -> GCS (immutable Bronze archival)
- Combined Pub/Sub + GCS (low latency + replayability)

## Standards

- Python with type hints.
- Structured logging via `shared.common.setup_cloud_logging`.
- Secrets via `shared.common.get_secret`.
- No hardcoded environment-specific values.

## Minimum module structure

```bash
ingestion/<domain>/<source>_<mode>/
├── main.py
├── requirements.txt
├── config.template.json
└── README.md
```

## Local quality checks

```bash
just lint
just type
just test
```

Deployment workflows are planned and will be documented once active.
