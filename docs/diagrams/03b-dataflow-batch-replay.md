# 03B Dataflow Batch/Replay View

> **Scope.** Batch and replay/backfill Dataflow path when it diverges
> from the stream path (different read pattern, merge-key dedup,
> upsert/merge to Silver). Target topology, not implementation
> blueprint. Pair with [`03a`](03a-dataflow-streaming.md) for the
> streaming path. Symbols:
> [conventions](README.md#diagram-conventions). Trade-offs:
> [`architecture.md`](../architecture.md).

```mermaid
flowchart LR
    classDef external  fill:#fef3c7,stroke:#d97706,stroke-width:1.5px,color:#78350f
    classDef compute   fill:#dbeafe,stroke:#1e40af,stroke-width:1.5px,color:#1e3a8a
    classDef storage   fill:#dcfce7,stroke:#166534,stroke-width:1.5px,color:#14532d
    classDef messaging fill:#fce7f3,stroke:#9d174d,stroke-width:1.5px,color:#831843
    classDef cross     fill:#f3f4f6,stroke:#4b5563,stroke-width:1.5px,color:#1f2937

    BZ["GCS Bronze"]:::storage --> READ["Batch Read"]:::compute
    READ --> PARSE["Parse + Contract Validation"]:::compute
    PARSE --> DEDUP["Merge-Key Dedup"]:::compute
    DEDUP --> UPSERT["Silver Upsert / Merge"]:::compute
    UPSERT --> SV["BigQuery Silver"]:::storage
    SV --> DQ["Quality Checks"]:::compute
    DQ --> GLD["BigQuery Gold (Recompute)"]:::storage

    PARSE --> ERR["Error Side Output"]:::cross
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
