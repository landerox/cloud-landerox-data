# 04 Cloud Functions Shared View

> **Scope.** Single Cloud Functions view when ingestion and trigger
> handlers are simple and tightly coupled. Target topology, not
> implementation blueprint. For independent deploy units, see
> [`04a`](04a-functions-ingestion-http.md) (ingestion) and
> [`04b`](04b-functions-trigger-orchestration.md) (trigger).
> Symbols: [conventions](README.md#diagram-conventions). Trade-offs:
> [`architecture.md`](../architecture.md).

```mermaid
flowchart LR
    classDef external  fill:#fef3c7,stroke:#d97706,stroke-width:1.5px,color:#78350f
    classDef compute   fill:#dbeafe,stroke:#1e40af,stroke-width:1.5px,color:#1e3a8a
    classDef storage   fill:#dcfce7,stroke:#166534,stroke-width:1.5px,color:#14532d
    classDef messaging fill:#fce7f3,stroke:#9d174d,stroke-width:1.5px,color:#831843
    classDef cross     fill:#f3f4f6,stroke:#4b5563,stroke-width:1.5px,color:#1f2937

    API["API / Webhook"]:::external --> ING["Ingestion Function"]:::compute
    ING -->|valid| PS["Pub/Sub"]:::messaging
    ING -->|archive raw| BZ["GCS Bronze"]:::storage
    ING -->|invalid| DLQ["DLQ"]:::cross

    EVT["Storage / Pub/Sub Events"]:::messaging --> TRG["Trigger Function"]:::compute
    TRG --> ORCH["Workflows / Scheduler Actions"]:::compute
    TRG --> CTRL["Replay / Control Topics"]:::messaging
    TRG -->|invalid| DLQ

    SEC["Secret Manager"]:::cross -.-> ING
    SEC -.-> TRG
    OBS["Logging + Monitoring"]:::cross -.-> ING
    OBS -.-> TRG
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
