# GCP Project Baseline Guide

## Purpose

Define a practical baseline for:

- GCP APIs that should be enabled
- Service account strategy for CI/CD and runtime modules

This baseline is intended for private runtime repositories aligned with a separate
Terraform infrastructure repository.

## Recommended API enablement

Enable APIs from the infrastructure repo (Terraform), not from ad-hoc scripts.

### Core platform APIs (recommended default)

| API service | Why it is needed |
| :--- | :--- |
| `serviceusage.googleapis.com` | API enable/disable management |
| `cloudresourcemanager.googleapis.com` | Project-level resource operations |
| `iam.googleapis.com` | IAM bindings and service account policies |
| `iamcredentials.googleapis.com` | Service account impersonation |
| `sts.googleapis.com` | Workload Identity Federation token exchange |
| `logging.googleapis.com` | Centralized logs |
| `monitoring.googleapis.com` | Metrics and alerting |
| `secretmanager.googleapis.com` | Secrets access for runtime modules |
| `storage.googleapis.com` | Bronze/DLQ/archive storage |
| `pubsub.googleapis.com` | Streaming ingestion and decoupling |
| `cloudfunctions.googleapis.com` | Cloud Functions deployment/runtime |
| `run.googleapis.com` | Cloud Functions Gen2 runtime dependency |
| `eventarc.googleapis.com` | Event-driven triggers (Gen2) |
| `dataflow.googleapis.com` | Beam/Dataflow jobs |
| `compute.googleapis.com` | Dataflow worker infrastructure |
| `bigquery.googleapis.com` | Silver/Gold analytical storage |
| `bigquerystorage.googleapis.com` | BigQuery high-throughput reads/writes |

### Conditional APIs (enable only when used)

| API service | Enable when |
| :--- | :--- |
| `artifactregistry.googleapis.com` | Storing custom images/templates |
| `cloudbuild.googleapis.com` | Building Dataflow Flex Templates in GCP |
| `cloudscheduler.googleapis.com` | Scheduled batch/replay triggers |
| `workflows.googleapis.com` | Orchestration and controlled retries |
| `vpcaccess.googleapis.com` | Private egress/network connectivity |
| `cloudkms.googleapis.com` | CMEK encryption requirements |
| `datastream.googleapis.com` | CDC ingestion from transactional databases |

## Service account model

### Separation of duties

- **CI/CD deployer identities (control plane):** deploy resources, no business data
  read access.
- **Runtime identities (data plane):** execute functions/pipelines with least
  privilege on Pub/Sub, GCS, BigQuery, and Secret Manager.
- **Google-managed service agents:** keep enabled; do not replace with default
  project service accounts.

### Recommended baseline by environment

| Service account | Role in platform | Recommendation |
| :--- | :--- | :--- |
| `sa-cicd-deployer-<env>` | Shared deployment identity | Minimum baseline |
| `sa-cicd-functions-<env>` | Functions-only deployment | Recommended at scale |
| `sa-cicd-dataflow-<env>` | Dataflow-only deployment | Recommended at scale |
| `sa-fn-<domain>-<env>` | Functions runtime | Recommended |
| `sa-df-<domain>-<env>` | Dataflow worker runtime | Recommended |
| `sa-orchestrator-<env>` | Workflows/Scheduler runtime | Optional but useful |

Practical count guidance:

- Small runtime (`<= 5` pipelines): `3-4` SAs per environment.
- Medium runtime (`5-20` pipelines): `6-12` SAs per environment.
- Large runtime (`20-50+` pipelines): `12+` SAs per environment.

### When to use one service account per data source

Create source-specific runtime SAs only when at least one condition is true:

- Different compliance boundary (for example PII vs non-PII).
- Different secret/API credential lifecycle and rotation ownership.
- Different IAM scope per source (separate buckets/datasets/topics).
- Independent auditability or incident isolation is required.

If none apply, use runtime SAs per domain (or per sensitivity tier), not per source.

## CI/CD recommendation

- Use **shared CI** for lint/type/test/security across all modules.
- Use **selective CD** by changed paths for `functions/**` and
  `dataflow/pipelines/**`.
- Keep deployment identities separate from runtime identities in all environments.

## Terraform alignment

Manage in the infrastructure repository:

- API enablement
- Service account creation
- IAM role bindings
- Workload Identity Federation providers and bindings

Runtime repositories should consume these identities and not redefine IAM topology.
