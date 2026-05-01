# ADR 0002: Selective Kappa Usage

- Status: Accepted
- Date: 2026-03-05

## Context

Kappa (single logic path for stream and replay) improves consistency but is not always the lowest-risk option for every domain. Some use cases have valid reasons to separate stream and batch behavior.

## Decision

Use Kappa selectively:

- Prefer Kappa when one transformation path can satisfy both real-time and backfill requirements.
- Use Lambda-lite split only when constraints differ materially (cost windows, source limitations, replay complexity, or compliance).

## Consequences

- Avoid statements such as "pure Kappa everywhere."
- Document per-pipeline rationale in module README files.
- Keep shared contracts consistent even when execution paths differ.
