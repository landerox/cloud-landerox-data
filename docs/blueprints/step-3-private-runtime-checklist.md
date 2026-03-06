# Step 3: Private Runtime Implementation Checklist

## Goal

Implement the first production runtime path in a **private repository** using the approved Step 2 scope, without exposing personal pipelines in this public baseline repository.

## Prerequisites (must be approved from Step 2)

- Scope document approved: [first-runtime-scope.md](first-runtime-scope.md)
- Contract v1 fields frozen
- Target SLOs accepted
- Governance baseline accepted
- Required APIs enabled in GCP project
- CI/CD and runtime service accounts provisioned by infrastructure repo
- Baseline templates reviewed:
  - `docs/blueprints/templates/contracts/source_events_v1.schema.json`
  - `docs/blueprints/templates/config/config.template.json`

## Recommended private repo structure

```bash
runtime-data-platform/
├── functions/
│   ├── ingestion/
│   │   └── <domain>/<source>_webhook/main.py
│   └── trigger/
│       └── <domain>/<event>_<purpose>/main.py
├── dataflow/
│   └── pipelines/
│       └── <domain>/
│           ├── bronze/<pipeline_name>/pipeline.py
│           ├── silver/<pipeline_name>/pipeline.py
│           └── gold/<pipeline_name>/pipeline.py
├── contracts/
│   └── <domain>/<data_product>.schema.json
├── tests/
│   ├── functions/<domain>/...
│   └── dataflow/<domain>/...
├── docs/
│   ├── runbooks/replay.md
│   ├── runbooks/backfill.md
│   └── slo/source_events_v1.md
└── .github/workflows/
    ├── ci.yml
    ├── functions-deploy.yml
    └── dataflow-deploy.yml
```

## Workstream checklist

### 1) Contract and schema

- [ ] Bootstrap contract from baseline template (`docs/blueprints/templates/contracts/source_events_v1.schema.json`)
- [ ] Create `contracts/source_events_v1.schema.json`
- [ ] Include required fields: `event_id`, `event_time`, `source`, `schema_version`, `payload`, `ingested_at`
- [ ] Define compatibility policy and migration notes for breaking changes

### 1.1) Runtime configuration bootstrap

- [ ] Bootstrap runtime config from baseline template (`docs/blueprints/templates/config/config.template.json`)
- [ ] Replace placeholders with environment-specific values in private repo
- [ ] Keep secrets out of git and resolve them from Secret Manager/WIF

### 2) Ingestion function (stream-first)

- [ ] Implement webhook/API handler
- [ ] Validate contract before publish
- [ ] Write immutable Bronze archive path (`gs://.../dt=YYYY-MM-DD/...`)
- [ ] Publish valid records to Pub/Sub
- [ ] Route invalid payloads with reason codes
- [ ] Enforce idempotency key (`event_id`)

### 3) Dataflow Silver pipeline

- [ ] Read from Pub/Sub (primary)
- [ ] Support GCS batch replay input (fallback)
- [ ] Apply typed transforms and deduplication
- [ ] Write to BigQuery Silver table
- [ ] Write errors to DLQ sink

### 4) Replay/backfill operations

- [ ] Implement DLQ replay job path
- [ ] Implement full backfill path from Bronze GCS
- [ ] Document trigger conditions and rollback strategy

### 5) Data quality and governance

- [ ] Bronze -> Silver checks (required fields, timestamps, type checks)
- [ ] Silver -> Gold checks (if Gold is enabled later)
- [ ] PII classification documented
- [ ] Retention windows configured (Bronze, DLQ, Silver)
- [ ] IAM boundary per dataset/table reviewed

### 6) Observability and SLO

- [ ] Structured logs in functions and pipelines
- [ ] Metrics: processed count, error count, latency
- [ ] Alerts for error rate and freshness breach
- [ ] SLO dashboard documented

### 7) CI/CD in private repo

- [ ] CI quality workflow (lint/type/test/security) for all modules
- [ ] Path-based selective CD for function deploys (`functions/**`)
- [ ] Path-based selective CD for Dataflow template build/deploy (`dataflow/pipelines/**`)
- [ ] Full regression/nightly validation workflow (separate from selective deploys)
- [ ] Environment-scoped secrets via WIF (no static keys)
- [ ] Deployment SAs separated from runtime SAs

## Verification gates

Run before enabling production traffic:

```bash
just lint
just type
just test
uv run pre-commit run --all-files
```

Also verify:

- [ ] Contract validation tests pass
- [ ] Replay test from DLQ passes
- [ ] Backfill test from Bronze sample passes
- [ ] p95 latency and freshness SLOs are measurable

## Rollout sequence

1. Deploy ingestion function with limited traffic.
2. Run Dataflow pipeline in low-volume mode.
3. Validate Silver outputs and DQ checks.
4. Test DLQ replay with synthetic invalid events.
5. Enable full traffic.
6. Run first weekly backfill drill.

## Definition of done

Step 3 is complete when:

1. Stream + batch fallback both run successfully.
2. Contract, idempotency, DLQ/replay, and observability are active.
3. CI/CD is operational in the private repo.
4. Runbooks exist and were exercised at least once.
