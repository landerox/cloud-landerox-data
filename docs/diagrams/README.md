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

## Diagram conventions

To keep the catalog readable as one body of work, every diagram uses
the same vocabulary. New diagrams must follow these rules.

### Direction

Default `flowchart LR` (left-to-right). Use a different direction only
when the topic is intrinsically vertical (storage hierarchy, layering).

### Canonical node IDs

| ID | Meaning |
| :--- | :--- |
| `SRC` | External sources |
| `API` | API / Webhook |
| `ING` | Ingestion Function |
| `TRG` | Trigger Function |
| `PS` | Pub/Sub |
| `CDC` | CDC Connectors |
| `BZ` | GCS Bronze |
| `BZBQ` | Bronze raw in BigQuery |
| `DF` | Dataflow |
| `SV` | BigQuery Silver |
| `BL` | BigLake External Tables |
| `ICE` | Iceberg Tables on GCS |
| `SQL` | SQL Transform Layer |
| `GLD` | BigQuery Gold |
| `DQ` | Data Quality Gates |
| `DLQ` | DLQ |
| `RPL` | Replay / Backfill Job |
| `OBS` | Logging + Monitoring |
| `SEC` | Secret Manager |
| `ORCH` | Scheduler / Workflows |

### Canonical stage labels

| Stage | Label |
| :--- | :--- |
| Validation | `Parse + Contract Validation` |
| Error side output | `Error Side Output` |
| DLQ sink | `DLQ` |
| Observability | `Logging + Monitoring` |

### Optional paths

Use dashed edges (`-. optional .->`, `-.->`) for:

- Optional storage targets (BigLake, Iceberg).
- Optional source patterns (CDC).
- Cross-cutting touch points (Secret Manager, Logging + Monitoring).
- Interoperability (Databricks).

Do **not** put `(optional)` inside node labels — let the edge style
carry that meaning.

### Mandatory controls in flow diagrams

Per [`architecture.md` § Minimum patterns](../architecture.md#minimum-patterns-must-have),
every diagram that shows record processing must include:

- Contract validation at the source boundary.
- DLQ side output for invalid records.
- Data quality gates between Silver and Gold.
- Observability touch points on every long-lived component.

A diagram that omits one of these is incomplete, not abbreviated. If
a control truly does not apply to that view, say so in the diagram's
preamble.

### Visual hierarchy (`classDef` categories)

Every node belongs to exactly one of five categories. Nodes get a
`:::class` suffix; the `classDef` block is replicated identically at
the top of each diagram so a reader does not need to import shared
state. The palette is chosen for legibility on GitHub light/dark.

| Category | Class | Used for |
| :--- | :--- | :--- |
| External | `external` | Sources, sinks, third-party systems (e.g. `SRC`, `API`, `DBX`, scheduler ticks, GCS-finalize events) |
| Compute | `compute` | Functions, Dataflow, transforms, gates, orchestration logic (e.g. `ING`, `TRG`, `DF`, `DQ`, `SQL`, `ORCH`) |
| Storage | `storage` | Persistent stores (e.g. `BZ`, `BZBQ`, `SV`, `BL`, `ICE`, `GLD`) |
| Messaging | `messaging` | Brokers and event channels (e.g. `PS`, `CDC`, control topics) |
| Cross-cutting | `cross` | Error / observability / secrets — does not carry primary data flow (`DLQ`, `ERR`, `OBS`, `SEC`) |

Canonical `classDef` block (copy verbatim into every diagram):

```text
classDef external  fill:#fef3c7,stroke:#d97706,stroke-width:1.5px,color:#78350f
classDef compute   fill:#dbeafe,stroke:#1e40af,stroke-width:1.5px,color:#1e3a8a
classDef storage   fill:#dcfce7,stroke:#166534,stroke-width:1.5px,color:#14532d
classDef messaging fill:#fce7f3,stroke:#9d174d,stroke-width:1.5px,color:#831843
classDef cross     fill:#f3f4f6,stroke:#4b5563,stroke-width:1.5px,color:#1f2937
```

### Scope note (every diagram)

Open each diagram with a short blockquote that frames the read. It
states what the view is, what it intentionally omits, and where to
go for trade-offs. It does **not** apologize for the diagram.

Template:

```markdown
> **Scope.** <one-line view purpose>. Target topology, not
> implementation blueprint. <one-line on what this view omits, if
> anything>. Symbols: see [conventions](README.md#diagram-conventions).
> Trade-offs and decisions: [`architecture.md`](../architecture.md).
```

### Legend (every diagram)

Every diagram closes with the same legend table, so a reader who
opens a single `.md` file in GitHub does not need to cross-reference
this README to decode it.

```markdown
| Symbol | Meaning |
| :--- | :--- |
| Solid arrow `-->` | Required path |
| Dashed arrow `-.->` | Cross-cutting touch point (observability, secrets) |
| Dashed labeled `-. text .->` | Optional path or out-of-band trigger (e.g. manual replay, optional storage target) |
| External | Source, sink, or third-party system |
| Compute | Function, Dataflow, transform, gate, orchestrator |
| Storage | GCS / BigQuery / Iceberg layer |
| Messaging | Broker or event channel |
| Cross-cutting | Error, observability, secrets — not on the happy path |
```

### When not to add a diagram

A diagram is the right tool for a topology, a flow with branching, or
a state machine. It is the wrong tool for the cases below -- keep them
in prose or tables instead:

- The same information fits in one table. Tables are easier to
  update, diff, and search than Mermaid source.
- The diagram needs more than ~12 nodes. Split by responsibility (one
  diagram per concern) or replace with prose.
- Labels need three or more lines each. Move the detail into the
  surrounding doc and shorten labels to a single phrase.
- The view is a near-duplicate of an existing one. Reuse and link
  instead -- diagram drift is the failure mode this catalog is
  designed to prevent.
