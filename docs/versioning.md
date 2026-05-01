# Versioning Policy

How we version this project, when we bump majors, and what consumers
should expect from each release line.

## Scheme

Strict [Semantic Versioning 2.0.0](https://semver.org/spec/v2.0.0.html).
Tags are formatted `vX.Y.Z` and applied by `cz bump` in
`.github/workflows/release.yml`. The `pyproject.toml` `version` field is
the single source of truth.

## Pre-1.0 stance (current)

The project is at `0.x.y`. **Any minor bump (`0.x → 0.(x+1)`) may carry
breaking changes** to the `shared.common` surface, the DLQ payload
shape, or the configuration schemas. Patch bumps (`0.x.y → 0.x.(y+1)`)
remain backward compatible within a minor.

This is intentional: the baseline still discovers its own contract by
being consumed in real runtime repos. Consumers of the pre-1.0 API
should pin **exactly** (`==`) in their `pyproject.toml`, not with a
caret/tilde range.

## When 1.0 lands

Cut `1.0.0` only when **all** of the following are true:

1. `shared.common.__all__` has been stable across two consecutive
   minor releases (no removals, no signature breaks).
2. The DLQ payload (`DLQPayload`) and the documented `reason_code`
   catalogue have been stable across two consecutive minor releases.
3. At least one private runtime repository has been running this
   baseline in production for one full month without needing a
   patch to `shared.common`.
4. The observability surface (`trace_context`, `parse_traceparent`,
   `current_traceparent`, `PipelineMetrics`) is wired end-to-end in a
   real pipeline.

The `1.0.0` release notes will explicitly enumerate the stable surface.
Anything outside that surface stays "implementation detail" and may
change without a major bump.

## Breaking change policy (post-1.0)

After `1.0.0`, breaking changes require **all** of:

- A migration runbook in the same PR, under
  `docs/migrations/<from>-to-<to>.md`.
- A deprecation cycle: the old API stays for at least one full minor
  release, emitting `DeprecationWarning` with a pointer to the
  migration runbook.
- A changelog entry under a `### Breaking` heading.

The release workflow is configured to refuse a major bump when the
changelog increment lacks a `### Breaking` section.

## Pre-release tags

For testing release-shape changes without exposing them to consumers,
use SemVer pre-release identifiers via `cz bump --increment MINOR
--prerelease alpha` (or `beta`/`rc`). Pre-release tags are formatted
`vX.Y.Z-alpha.N` and are excluded from the "latest" GitHub Release
marker.

## Patch-only fix windows

When a release introduces a regression that warrants a hot fix, the
patch bump targets the most recent minor only. Older minors are not
back-ported unless explicitly listed under "Supported Versions" in
[`.github/SECURITY.md`](../.github/SECURITY.md).

## Compatibility matrix (planned)

Once the first stable runtime is live, we will publish a matrix of
which baseline versions support which Python / Apache Beam / GCP SDK
combinations. Until then, the supported combination is the one locked
in `uv.lock` for the corresponding tag.

## Verification

The release workflow attaches both a CycloneDX SBOM and a SLSA build
provenance attestation to every GitHub Release (see
[CI/CD Guide](cicd.md#active-workflows)). Consumers should verify
provenance with `gh attestation verify` before installing in a
sensitive environment.

## Related

- [CI/CD Guide](cicd.md)
- [`.github/SECURITY.md`](../.github/SECURITY.md)
- [`CHANGELOG.md`](../CHANGELOG.md)
