# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-01-10

### Added

- **Initial Public Release:** Standardized serverless ETL framework for GCP data processing.
- **Microservices:** Implementation of 8 high-frequency ingestion functions and 1 batch data loader (GCS to BigQuery).
- **Resilience:** Integrated `tenacity` for exponential backoff and retry logic in external API calls.
- **Concurrency:** Implemented **Optimistic Locking** using GCS generation numbers to prevent data race conditions.
- **Security:** Automated configuration reconstruction in CI/CD using Base64-encoded GitHub Secrets.
- **Quality Control:** Integrated `pre-commit` hooks for `ruff` (linting/formatting), `gitleaks` (secret detection), and `markdownlint`.
- **CI/CD:** Matrix-based selective deployment workflow using GitHub Actions.
