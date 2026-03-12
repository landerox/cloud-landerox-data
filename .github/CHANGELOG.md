# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- Documentation now clearly separates current state from target architecture.
- Architecture language aligned to a pragmatic hybrid model (warehouse + lakehouse, batch + streaming).

## [0.1.0] - 2026-01-10

### Added

- Initial repository scaffolding for:
  - Cloud Functions modules
  - Dataflow modules
  - Shared utilities
  - Testing and quality tooling (`ruff`, `ty`, `pytest`, `pre-commit`)
- Initial CI quality workflow (`lint.yml`).
