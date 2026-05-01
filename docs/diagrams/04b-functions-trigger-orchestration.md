# 04B Cloud Functions Trigger/Orchestration

> **Scope.** Trigger/orchestration handlers as independent deploy
> units, fed by event sources (GCS finalize, Pub/Sub control,
> scheduler ticks). Target topology, not implementation blueprint.
> Pair with [`04a`](04a-functions-ingestion-http.md) when ingestion
> is also independent. Symbols:
> [conventions](README.md#diagram-conventions). Trade-offs:
> [`architecture.md`](../architecture.md).

```mermaid
flowchart LR
    classDef external  fill:#fef3c7,stroke:#d97706,stroke-width:1.5px,color:#78350f
    classDef compute   fill:#dbeafe,stroke:#1e40af,stroke-width:1.5px,color:#1e3a8a
    classDef storage   fill:#dcfce7,stroke:#166534,stroke-width:1.5px,color:#14532d
    classDef messaging fill:#fce7f3,stroke:#9d174d,stroke-width:1.5px,color:#831843
    classDef cross     fill:#f3f4f6,stroke:#4b5563,stroke-width:1.5px,color:#1f2937

    EV1["GCS Finalize Event"]:::external --> TRG["Trigger Function"]:::compute
    EV2["Pub/Sub Control Event"]:::external --> TRG
    EV3["Scheduler Tick"]:::external --> TRG

    TRG --> WF["Workflows"]:::compute
    TRG --> DFSTART["Dataflow Job Start"]:::compute
    TRG --> RPL["Replay Invocation"]:::compute
    TRG -->|invalid| DLQ["DLQ"]:::cross

    SEC["Secret Manager"]:::cross -.-> TRG
    OBS["Logging + Monitoring"]:::cross -.-> TRG
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
