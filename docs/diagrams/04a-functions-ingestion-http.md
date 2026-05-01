# 04A Cloud Functions Ingestion HTTP/Webhook

> **Scope.** Ingestion handler as an independent runtime unit (its
> own deploy/ownership). Target topology, not implementation
> blueprint. Pair with
> [`04b`](04b-functions-trigger-orchestration.md) when triggers are
> also independent. Symbols:
> [conventions](README.md#diagram-conventions). Trade-offs:
> [`architecture.md`](../architecture.md).

```mermaid
flowchart LR
    classDef external  fill:#fef3c7,stroke:#d97706,stroke-width:1.5px,color:#78350f
    classDef compute   fill:#dbeafe,stroke:#1e40af,stroke-width:1.5px,color:#1e3a8a
    classDef storage   fill:#dcfce7,stroke:#166534,stroke-width:1.5px,color:#14532d
    classDef messaging fill:#fce7f3,stroke:#9d174d,stroke-width:1.5px,color:#831843
    classDef cross     fill:#f3f4f6,stroke:#4b5563,stroke-width:1.5px,color:#1f2937

    SRC["External API / Webhook"]:::external --> AUTH["Auth + Basic Validation"]:::compute
    AUTH --> ING["Ingestion Function"]:::compute
    ING -->|valid| PS["Pub/Sub"]:::messaging
    ING -->|archive raw| BZ["GCS Bronze"]:::storage
    ING -->|invalid| DLQ["DLQ"]:::cross

    SEC["Secret Manager"]:::cross -.-> ING
    OBS["Logging + Monitoring"]:::cross -.-> ING
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
