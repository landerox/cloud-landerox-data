# 05 Storage Model Hybrid (BigQuery + Lakehouse)

> **Scope.** Storage layout for the hybrid platform — BigQuery native
> as default delivery target, BigLake/Iceberg as opt-in for
> interoperability and file-based workloads. Edges represent logical
> data flow between layers; processing (Dataflow / SQL) is shown as
> labels rather than nodes to keep the focus on storage. For the
> processing detail see [`03`](03-dataflow-shared.md). Symbols:
> [conventions](README.md#diagram-conventions). Trade-offs:
> [`architecture.md`](../architecture.md).

```mermaid
flowchart LR
    classDef external  fill:#fef3c7,stroke:#d97706,stroke-width:1.5px,color:#78350f
    classDef compute   fill:#dbeafe,stroke:#1e40af,stroke-width:1.5px,color:#1e3a8a
    classDef storage   fill:#dcfce7,stroke:#166534,stroke-width:1.5px,color:#14532d
    classDef messaging fill:#fce7f3,stroke:#9d174d,stroke-width:1.5px,color:#831843
    classDef cross     fill:#f3f4f6,stroke:#4b5563,stroke-width:1.5px,color:#1f2937

    BZ["GCS Bronze"]:::storage -->|via Dataflow| SV["BigQuery Silver"]:::storage
    BZ -. optional .-> ICE["Iceberg Tables on GCS"]:::storage

    ICE --> BL["BigLake External Tables"]:::storage
    SV --> SQL["SQL Transform Layer"]:::compute
    BL -. optional .-> SQL
    SQL --> GLD["BigQuery Gold"]:::storage

    DBX["Databricks on GCP"]:::external -. interoperable .-> ICE
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
