# Diagram Catalog

## Purpose

Define a stable diagram set for this architecture baseline.

This keeps diagrams focused and avoids over-documenting the same flow in multiple
variants.

## Recommended set

Use this baseline set:

1. Context overview
2. End-to-end flow with controls
3. Dataflow processing view (`1` or `2` diagrams)
4. Cloud Functions view (`1` or `2` diagrams)
5. Hybrid storage/model view (BigQuery + Lakehouse/Iceberg)

## Dataflow: when to use 1 vs 2 diagrams

Use **one** Dataflow diagram when streaming and batch/replay share most transforms.

Use **two** Dataflow diagrams when they differ materially in:

- input contracts/parsing
- watermark/windowing behavior
- dedup/replay strategies
- sink/write mode behavior

Templates:

- Shared view: [03-dataflow-shared.md](03-dataflow-shared.md)
- Streaming view: [03a-dataflow-streaming.md](03a-dataflow-streaming.md)
- Batch/replay view: [03b-dataflow-batch-replay.md](03b-dataflow-batch-replay.md)

## Cloud Functions: when to use 1 vs 2 diagrams

Use **one** Functions diagram when ingestion and trigger handlers are simple and
coupled in one runtime concern.

Use **two** Functions diagrams when ingestion and event-trigger/orchestration
handlers are independent deploy/ownership units.

Templates:

- Shared view: [04-functions-shared.md](04-functions-shared.md)
- Ingestion HTTP/Webhook: [04a-functions-ingestion-http.md](04a-functions-ingestion-http.md)
- Trigger/Orchestration: [04b-functions-trigger-orchestration.md](04b-functions-trigger-orchestration.md)

## Diagram files

- [01-context-overview.md](01-context-overview.md)
- [02-e2e-controls.md](02-e2e-controls.md)
- [03-dataflow-shared.md](03-dataflow-shared.md)
- [03a-dataflow-streaming.md](03a-dataflow-streaming.md)
- [03b-dataflow-batch-replay.md](03b-dataflow-batch-replay.md)
- [04-functions-shared.md](04-functions-shared.md)
- [04a-functions-ingestion-http.md](04a-functions-ingestion-http.md)
- [04b-functions-trigger-orchestration.md](04b-functions-trigger-orchestration.md)
- [05-storage-hybrid-bq-lakehouse.md](05-storage-hybrid-bq-lakehouse.md)
