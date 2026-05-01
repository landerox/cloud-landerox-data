# 03A Dataflow Streaming View

> **Scope.** Streaming-only Dataflow path when window, watermark, or
> latency constraints differ materially from batch. Target topology,
> not implementation blueprint. Pair with
> [`03b`](03b-dataflow-batch-replay.md) for the batch/replay path.
> Symbols: [conventions](README.md#diagram-conventions). Trade-offs:
> [`architecture.md`](../architecture.md).

```mermaid
flowchart LR
    classDef external  fill:#fef3c7,stroke:#d97706,stroke-width:1.5px,color:#78350f
    classDef compute   fill:#dbeafe,stroke:#1e40af,stroke-width:1.5px,color:#1e3a8a
    classDef storage   fill:#dcfce7,stroke:#166534,stroke-width:1.5px,color:#14532d
    classDef messaging fill:#fce7f3,stroke:#9d174d,stroke-width:1.5px,color:#831843
    classDef cross     fill:#f3f4f6,stroke:#4b5563,stroke-width:1.5px,color:#1f2937

    PS["Pub/Sub"]:::messaging --> PARSE["Parse + Contract Validation"]:::compute
    PARSE --> WM["Window / Watermark"]:::compute
    WM --> DEDUP["Keyed Dedup"]:::compute
    DEDUP --> ENRICH["Streaming Enrichment"]:::compute
    ENRICH --> SV["BigQuery Silver (Streaming)"]:::storage
    SV --> DQ["Quality Checks"]:::compute
    DQ --> GLD["BigQuery Gold (Incremental)"]:::storage

    PARSE --> ERR["Error Side Output"]:::cross
    WM --> ERR
    DEDUP --> ERR
    ERR --> DLQ["DLQ"]:::cross
```

| Symbol | Meaning |
| :--- | :--- |
| Solid arrow `-->` | Required path |
| Dashed arrow `-.->` | Cross-cutting touch point (observability, secrets) |
| Dashed labeled `-. text .->` | Optional path or out-of-band trigger |
| External | Source, sink, or third-party system |
| Compute | Function, Dataflow, transform, gate, orchestrator |
| Storage | GCS / BigQuery / Iceberg layer |
| Messaging | Broker or event channel |
| Cross-cutting | Error, observability, secrets — not on the happy path |
