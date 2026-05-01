# 02 End-to-End Flow With Controls

> **Scope.** Same path as [`01`](01-context-overview.md), with the
> cross-cutting controls made explicit: contract validation at the
> source boundary, DLQ + replay, data-quality gates between layers,
> and observability touch points. Target topology, not implementation
> blueprint. Optional paths (CDC, BigLake/Iceberg, direct
> Pub/Sub→BigQuery) are intentionally omitted to keep the focus on
> controls — see [`01`](01-context-overview.md) for full topology.
> Symbols: [conventions](README.md#diagram-conventions). Trade-offs:
> [`architecture.md`](../architecture.md).

```mermaid
flowchart LR
    classDef external  fill:#fef3c7,stroke:#d97706,stroke-width:1.5px,color:#78350f
    classDef compute   fill:#dbeafe,stroke:#1e40af,stroke-width:1.5px,color:#1e3a8a
    classDef storage   fill:#dcfce7,stroke:#166534,stroke-width:1.5px,color:#14532d
    classDef messaging fill:#fce7f3,stroke:#9d174d,stroke-width:1.5px,color:#831843
    classDef cross     fill:#f3f4f6,stroke:#4b5563,stroke-width:1.5px,color:#1f2937

    subgraph INGEST["Ingestion (with contract validation)"]
        API["API / Webhook"]:::external
        ING["Ingestion Function"]:::compute
        PS["Pub/Sub"]:::messaging
        BZ["GCS Bronze"]:::storage
    end

    subgraph PROCESS["Processing (with quality gates)"]
        DF["Dataflow"]:::compute
        SV["BigQuery Silver"]:::storage
        DQ["Data Quality Gates"]:::compute
        GLD["BigQuery Gold"]:::storage
    end

    subgraph RECOVERY["Recovery"]
        DLQ["DLQ"]:::cross
        RPL["Replay / Backfill Job"]:::compute
    end

    subgraph CROSSCUT["Cross-cutting"]
        OBS["Logging + Monitoring"]:::cross
    end

    API --> ING
    ING -->|valid raw| BZ
    ING -->|publish valid| PS
    ING -->|invalid| DLQ

    PS --> DF
    BZ --> DF
    DLQ -. manual replay .-> RPL
    RPL --> DF

    DF -->|valid records| SV
    DF -->|invalid records| DLQ
    SV --> DQ
    DQ --> GLD

    ING -.-> OBS
    DF -.-> OBS
    DQ -.-> OBS
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
