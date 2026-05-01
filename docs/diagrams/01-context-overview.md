# 01 Context Overview

> **Scope.** End-to-end target topology of the hybrid platform —
> sources, ingestion paths, processing, and Medallion storage. Target
> topology, not implementation blueprint. CDC, BigLake/Iceberg, and
> direct Pub/Sub→BigQuery are shown as dashed (opt-in) paths; pick
> per source/SLA per the
> [decision matrix](../architecture.md#decision-matrix). For the
> control overlay (validation, DLQ, DQ gates) see
> [`02`](02-e2e-controls.md). Symbols:
> [conventions](README.md#diagram-conventions). Trade-offs:
> [`architecture.md`](../architecture.md).

```mermaid
flowchart LR
    classDef external  fill:#fef3c7,stroke:#d97706,stroke-width:1.5px,color:#78350f
    classDef compute   fill:#dbeafe,stroke:#1e40af,stroke-width:1.5px,color:#1e3a8a
    classDef storage   fill:#dcfce7,stroke:#166534,stroke-width:1.5px,color:#14532d
    classDef messaging fill:#fce7f3,stroke:#9d174d,stroke-width:1.5px,color:#831843
    classDef cross     fill:#f3f4f6,stroke:#4b5563,stroke-width:1.5px,color:#1f2937

    subgraph SOURCES["Sources"]
        SRC["External Sources"]:::external
    end

    subgraph INGEST["Ingestion"]
        ING["Ingestion Function"]:::compute
        PS["Pub/Sub"]:::messaging
        CDC["CDC Connectors"]:::messaging
    end

    subgraph PROCESS["Processing"]
        DF["Dataflow"]:::compute
        SQL["SQL Transform Layer"]:::compute
    end

    subgraph STORAGE["Storage (Medallion)"]
        BZ["GCS Bronze"]:::storage
        BZBQ["Bronze raw in BigQuery"]:::storage
        SV["BigQuery Silver"]:::storage
        BL["BigLake / Iceberg Silver"]:::storage
        GLD["BigQuery Gold"]:::storage
    end

    subgraph CROSSCUT["Cross-cutting"]
        ORCH["Scheduler / Workflows"]:::compute
        SEC["Secret Manager"]:::cross
        OBS["Logging + Monitoring"]:::cross
    end

    SRC --> ING
    SRC --> PS
    SRC -. optional .-> CDC

    ING --> BZ
    ING --> PS
    PS -. optional .-> BZBQ

    BZ --> DF
    PS --> DF
    CDC -. optional .-> DF

    DF --> SV
    DF -. optional .-> BL

    BZBQ -. optional .-> SQL
    SV --> SQL
    BL -. optional .-> SQL
    SQL --> GLD

    ORCH --> ING
    ORCH --> DF

    SEC -.-> ING
    SEC -.-> DF
    OBS -.-> ING
    OBS -.-> DF
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
