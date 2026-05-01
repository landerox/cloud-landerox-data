# Decision Records & References

Decisions in this repo live in **three places, by purpose**. Pick the
right one when adding a new entry — duplicating across them is the
fastest way to make the documentation rot.

| Type | Where | Format |
| :--- | :--- | :--- |
| **Architecture decisions** | `docs/adr/0NNN-*.md` (this folder) | MADR — Status, Context, Decision, Considered alternatives, Consequences |
| **Tool choices** (uv vs poetry, pyright vs mypy, ...) | [`docs/tech-stack.md`](../tech-stack.md) | Categorised table: Tool / Why / Alternatives considered |
| **Operational axes** (sink, mode, topology, ...) | [`docs/architecture.md`](../architecture.md#decision-matrix) § Decision Matrix | Axis × preferred × alternate × use-when |

## Architecture Decision Records

- [0001 — Hybrid GCP Data Platform](0001-hybrid-gcp-data-platform.md)
  — sets the warehouse + lakehouse stance and the layering pattern
  (Medallion + alternatives considered)
- [0002 — Selective Kappa Usage](0002-kappa-when-to-use.md)
  — when single-path streaming logic replaces a Lambda-style split
- [0003 — Storage and Table Format Strategy](0003-storage-table-format-strategy.md)
  — file formats per layer, BigQuery native vs BigLake/Iceberg trade-off
- [0004 — Batch + Streaming Operating Model](0004-batch-streaming-operating-model.md)
  — dual operating modes, replay/backfill expectations

The `tests/test_doc_coherence.py::test_every_adr_is_listed_in_adr_index`
test fails CI if a new ADR file is added without an entry above.

## When to add a new ADR vs extend an existing doc

| Change | Where it goes |
| :--- | :--- |
| Adopting a new architectural pattern, deprecating one, or changing the operating model | **New ADR** here |
| Swapping a tool, adding a new tool category, removing a tool | New row (or table) in [`docs/tech-stack.md`](../tech-stack.md) |
| New choice axis (e.g. "encryption mode", "naming convention") with a default + alternates | New row in the Decision Matrix in [`docs/architecture.md`](../architecture.md#decision-matrix) |
| Updating an existing decision because the world changed | Mark the old ADR `Superseded by ADR-NNNN`, write a new ADR; do not edit the old one in place |

## ADR conventions

- Filename: `NNNN-<short-kebab-case-title>.md`, zero-padded sequence.
- Status values: `Proposed`, `Accepted`, `Superseded by ADR-NNNN`,
  `Deprecated`.
- Date in `YYYY-MM-DD`. Use the date of acceptance, not the date of
  drafting.
- Keep accepted ADRs **immutable**: only metadata (status, links) may
  be updated after acceptance. Substantive changes go in a new ADR.
