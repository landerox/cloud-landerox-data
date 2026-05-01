# Tech Stack

Inventory of every tool wired into this repository, why it was chosen,
and what was considered before settling on it. Versions live in
`pyproject.toml`, `.pre-commit-config.yaml`, `.devcontainer/Dockerfile`,
and `.github/workflows/*.yml` (auto-bumped by Dependabot); they are
intentionally absent here so the doc stays evergreen.

## Guiding values

- **Astral-first** for the Python toolchain (`uv`, `ruff`):
  consistent vendor, single binary distribution, fast feedback. The
  type checker (`pyright`) lives outside the Astral stack on purpose
  -- see "When to revisit" for the rationale.
- **Conventional Commits everywhere**: enforced by `commitizen` on
  `commit-msg`, mirrored by `dependabot` PR prefixes (`build` / `chore` /
  `ci`).
- **Supply chain transparent**: SBOM, SLSA provenance, license gate, two
  SAST engines, Scorecard public dashboard.
- **DX over ceremony**: devcontainer with emulators, `just` recipes that
  mirror CI exactly, no hidden steps.

## Build & Package

| Tool | Why | Alternatives considered |
| :--- | :--- | :--- |
| **uv** | Single binary, lockfile-driven, ~10x faster than pip+venv; same vendor as `ruff`. | `pip + venv` (slow, no lock), `poetry` (slower resolver, JSON-RPC plugin model), `pdm` (smaller ecosystem). |
| **hatchling** | Modern PEP 517 backend, no `setup.py`, native to `pyproject.toml`. | `setuptools` (legacy boilerplate), `poetry-core` (couples you to poetry), `flit-core` (less flexible for src-layout). |

## Lint & Format

| Tool | Why | Alternatives considered |
| :--- | :--- | :--- |
| **ruff (check)** | Replaces flake8 + isort + pycodestyle + pyupgrade + several plugins in one Rust binary. | `flake8 + plugins` (slow, fragmented), `pylint` (slow, opinionated), `prospector` (meta-runner overhead). |
| **ruff (format)** | Same engine as the linter; black-compatible style without the extra dependency. | `black` (separate tool, slower), `autopep8` (incomplete), `yapf` (less adopted). |
| **pyright** (strict mode) | Same engine as VS Code Pylance, so editor and CI report identical findings. Native Pydantic v2 + Beam generic inference, mature, vendor-stable. | `mypy` (mature but slower, requires per-lib plugins like `pydantic.mypy`), `ty` (Astral, but still pre-1.0 with limited Pydantic/Beam support — used initially, migrated when pre-1.0 churn became a risk). |
| **hadolint** | De-facto Dockerfile linter; catches DL-coded smells (`pipefail`, apt cleanup, version pin guidance). | No widely adopted alternative. |
| **shellcheck** | The standard for shell quality; catches quoting, exit-code, and trap bugs. | `bashate` (PEP-8-style only, weaker checks). |
| **yamllint** | Catches indentation, truthy quirks, and trailing whitespace before CI parses them. | Schema-only validators (don't catch style). |
| **markdownlint-cli** | Stable, opinionated, configurable; auto-fixes most issues. | `markdownlint-cli2` (newer, no clear win for our scale), `vale` (broader but heavier setup), `prettier` (different style philosophy). |
| **actionlint** | Validates GitHub Actions workflows locally before push; catches expression and shell injection issues. | No widely adopted alternative. |

## Test

| Tool | Why | Alternatives considered |
| :--- | :--- | :--- |
| **pytest** | Function-style tests, fixtures, parametrize, strict markers; ecosystem standard. | `unittest` (stdlib but verbose, class-bound), `nose2` (low maintenance). |
| **pytest-cov** | Native pytest integration, branch coverage, XML for Codecov. | `coverage.py` standalone (manual integration). |
| **hypothesis** | Property-based testing — found a real bug in `validate_contract` test on first run. | `faker` (random generation, no shrinking), `schemathesis` (HTTP-only). |
| **pytest-benchmark** | Micro-benchmarks with regression tracking; gated by `-m benchmark` so they do not bloat PR runs. | `timeit` (manual), `asv` (overkill for shared utilities). |
| **mutmut** | Mutation testing measures test quality, not just line coverage; informational nightly. | `cosmic-ray` (slower, less maintained), `mutpy` (abandoned). |
| **freezegun** | Deterministic time in tests for `datetime.now`-dependent paths. | `time-machine` (faster, but smaller adoption). |

## Security & Supply Chain

| Tool | Why | Alternatives considered |
| :--- | :--- | :--- |
| **CodeQL** | Deep dataflow SAST, native GitHub integration, official `security-and-quality` ruleset. | `Snyk` (commercial), `SonarCloud` (heavier, separate UI). |
| **Semgrep** | Faster than CodeQL, Python-specific rules CodeQL misses, anonymous mode (no account). | Relying on CodeQL alone (misses some Python idioms). |
| **Trivy** | Single tool covers both Dockerfile/IaC config and image CVE scans; SARIF native. | `grype` (image only), `anchore` (heavier), `snyk-container` (commercial). |
| **OpenSSF Scorecard** | Industry-standard supply-chain posture score, public dashboard, no install. | None at this maturity level. |
| **pip-audit** | PyPA-maintained dependency CVE scanner, JSON/SARIF output, `--require-hashes` ready. | `safety` (commercial-leaning, smaller DB). |
| **gitleaks** | Single secrets scanner: actively maintained, broad pattern catalogue, no baseline file required. | `detect-secrets` (used initially in parallel; removed because the dual-scan was redundant and its baseline file was maintenance overhead), `trufflehog` (broader patterns, noisier). |
| **License gate** (custom script + `pip-licenses`) | Lets us encode a permissive-only allowlist with a per-package exception list, instead of pinning to a third-party policy engine. | `liccheck`, `pip-licenses --fail-on` (lacks per-package allowlist). |

## Release & Provenance

| Tool | Why | Alternatives considered |
| :--- | :--- | :--- |
| **commitizen** | Bumps version + changelog from Conventional Commits in one command; `commit-msg` hook validates author commits. | `semantic-release` (Node ecosystem), `bump2version` (no changelog). |
| **cyclonedx-bom** | CycloneDX is the OSS-friendly SBOM format; introspects the locked Python env via `cyclonedx_py environment`. | `syft` (broader format support, heavier), `spdx-tools` (SPDX format, less BOM-focused). |
| **actions/attest-build-provenance** | First-party GitHub action for SLSA L3 provenance via sigstore, no extra infrastructure. | `slsa-github-generator` (more configuration overhead). |

## Developer Experience

| Tool | Why | Alternatives considered |
| :--- | :--- | :--- |
| **Devcontainers (`mcr.microsoft.com/devcontainers/python:1-3.13-bookworm`)** | Reproducible IDE environment, broad VS Code support, official Microsoft image. | Custom Dockerfile from scratch (more maintenance), Nix flake (steeper learning). |
| **gcloud SDK** | Required for emulators, manual ops, Workload Identity Federation. | None. |
| **Pub/Sub emulator** | Official local emulator, no GCP credentials required. | `LocalStack` (AWS-focused), shelling out to a real project (cost + latency). |
| **`just`** | Modern command runner with simple syntax, cross-platform, no `tab vs space` traps. | `make` (legacy syntax, tab-only), npm scripts (Node ecosystem), shell aliases (no portability). |

## CI/CD Orchestration

| Tool | Why | Alternatives considered |
| :--- | :--- | :--- |
| **GitHub Actions** | Native to repo host, free for public repos, large action ecosystem. | `CircleCI` / `GitLab CI` (different host), `Jenkins` (self-hosted overhead). |
| **Dependabot** | Native to GitHub, supports `pip`, `github-actions`, `docker`, `devcontainers` ecosystems with cooldown + grouping. | `Renovate` (more flexible config but extra bot to install). |
| **lychee** | Rust-based link checker; fast, cache-aware, simple GitHub action. | `markdown-link-check` (Node, slower), `liche` (Go, less maintained). |

## Runtime Libraries (production deps)

| Tool | Why | Alternatives considered |
| :--- | :--- | :--- |
| **apache-beam** | Required SDK for Dataflow runner; Cloud-native + portable to other runners. | None (Dataflow contract). |
| **functions-framework** | Official Functions Gen 2 runtime adapter. | None. |
| **google-cloud-bigquery / pubsub / secret-manager / storage** | Official Google client libraries; required for first-class auth, retries, async. | Generic HTTP clients (skip integrated retries / IAM). |
| **pydantic v2** | Performance-rewritten core, native `model_validate`, broad ecosystem (FastAPI, Beam contracts). | `marshmallow` (slower, separate validation/serialization), `attrs` (no validation), `dataclasses` (no validation). |

## When to revisit

- **`ty` reaches 1.0 with full Pydantic + Beam support**: re-evaluate vs the current `pyright`. The migration cost is small (the config layout is similar) and the consistency win (same vendor as `uv`/`ruff`) would be real.
- **A tool drops out of active maintenance**: covered by Dependabot PR cadence — a stale repo will surface as no PRs over weeks.
- **Adding a new category** (e.g. dashboards, profiling): document the choice here in a new table before merging the dependency.

## Related

- [CI/CD Guide](cicd.md) — workflow inventory, branch protection, definition of done.
- [Versioning Policy](versioning.md) — when we bump majors, pre-1.0 stance.
- [Coding Style](guides/coding-style.md) — what `ruff` and `pyright` enforce.
- [Security (developer)](guides/security.md) — how the security tools above are wired into review.
