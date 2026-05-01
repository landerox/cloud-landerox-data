# Security Guide (for developers)

Security rules that apply while **writing, reviewing, and shipping code** in
this repository.

This document is distinct from [`.github/SECURITY.md`](../../.github/SECURITY.md),
which covers **vulnerability reporting**. Contact procedures for disclosed
vulnerabilities live there.

## 1) Secrets

- **Never commit secrets.** API keys, service-account JSON, passwords,
  connection strings, or signed URLs do not belong in the repo, in CI
  logs, in test fixtures, or in example config.
- Read secrets via `shared.common.get_secret`. Do not instantiate
  `SecretManagerServiceClient` directly in modules outside
  `shared/common/secrets.py`.
- Local development: use `.env` (gitignored) or the devcontainer
  environment. `GOOGLE_CLOUD_PROJECT` is set automatically by the
  devcontainer; other values are injected at runtime.
- Committed templates use the `.template.json` suffix and must contain
  only placeholders.

Enforcement:

- `gitleaks` (pre-commit) with `.config/gitleaks.toml`. Single secrets scanner; no second tool needed for this scale.
- `check-added-large-files` (pre-commit) to block accidental binary
  payloads.

If a secret is committed by accident: **rotate it immediately**, then
rewrite history or invalidate the exposed credential. The rewrite alone
does not undo the leak.

## 2) Input validation

- Every payload coming from outside the trust boundary (HTTP request,
  Pub/Sub message, GCS object content, BigQuery federation) must be
  validated with a **Pydantic v2** model via
  `shared.common.validate_contract`.
- Validation failures route to DLQ with a stable `reason_code`
  (see [error-handling.md](error-handling.md)).
- Do not trust upstream systems to enforce schema — the contract lives in
  this repo.

## 3) SQL

- **Parameterized queries only.** String concatenation or f-strings to
  build SQL is forbidden, even for internal constants.
- Prefer BigQuery's `QueryJobConfig.query_parameters` with
  `ScalarQueryParameter` / `ArrayQueryParameter`.
- Table references are fully qualified: `` `project.dataset.table` ``.

Example:

```python
from google.cloud import bigquery

client = bigquery.Client()
job_config = bigquery.QueryJobConfig(
    query_parameters=[
        bigquery.ScalarQueryParameter("event_id", "STRING", event_id),
    ],
)
client.query(
    "SELECT 1 FROM `project.dataset.events` WHERE event_id = @event_id",
    job_config=job_config,
)
```

## 4) Logging and PII

- Do not log full payloads by default. Log **identifiers**
  (`event_id`, `user_id`, `schema_version`, `source`) and **counts**.
- If you must log a payload for debugging, gate it behind an env flag
  (`DEBUG_LOG_PAYLOADS=1`) and ensure it is redacted for classified PII
  fields (email, phone, address, card data, government IDs).
- Redact secrets from exception messages before logging:
  `str(err).replace(secret_value, "***")` is a last resort — prefer not
  interpolating secrets into messages in the first place.
- Structured logging (`extra_fields`) is the canonical path; see
  [observability.md](observability.md).

## 5) Least privilege

- Each runtime (function or pipeline) uses a dedicated service account
  with the narrowest IAM role set required.
- No reuse of the Compute Engine default service account.
- Forbidden roles outside explicit justification:
  `roles/owner`, `roles/editor`, `roles/iam.securityAdmin`.
- Prefer predefined roles over `Admin` variants when a task-scoped role
  exists (e.g. `roles/bigquery.dataEditor` instead of `bigquery.admin`).

IAM identities and their bindings are provisioned in the separate
Terraform repository; see
[gcp-project-baseline.md](gcp-project-baseline.md) for the interface.

## 6) CI/CD authentication

- Use **Workload Identity Federation (WIF)** from GitHub Actions to GCP.
- **No static service-account JSON keys** in the repo, in Secrets, or in
  CI logs.
- Environment-scoped GitHub Secrets/Variables for per-env configuration.
- CI tokens must be scoped to the minimum permissions required by the job
  (`permissions:` block in every workflow).

See [cicd.md](../cicd.md) for the current posture.

## 7) Dependencies

- Add dependencies only when necessary. Prefer the standard library.
- Lock with `uv.lock`; CI uses `uv sync --frozen`.
- `pip-audit` runs in pre-commit (pre-push stage) and CI. A failing audit
  blocks the merge.
- License compliance is enforced in CI via
  `.github/scripts/check_licenses.py`: only permissive licenses (MIT,
  BSD, Apache, ISC, MPL, PSF, Unlicense, Public Domain, Zlib, CC0,
  HPND, 0BSD) pass. Strong copyleft (GPL/AGPL/LGPL/SSPL/EUPL) and
  unknown licenses fail the merge. Per-package allowlist exists for
  metadata false positives.
- Dependabot (`.github/dependabot.yml`) automates weekly version bumps
  for `pip`, `github-actions`, `devcontainers`, and `docker`.
- SAST: CodeQL (`security-and-quality`) and Semgrep
  (`p/python` + `p/security-audit` + `p/secrets`) both upload SARIF to
  the Security tab and run on every PR.
- Container hygiene: Trivy scans the devcontainer Dockerfile + IaC on
  every PR (blocking on CRITICAL/HIGH) and the built image weekly
  (informational).

Review checklist when adding a dependency:

- Is it maintained (recent releases, active issues)?
- License in the allowlist (the CI license gate enforces this)?
- Does it ship C extensions requiring system libs the devcontainer lacks?
- Does it add a known CVE (`pip-audit`)?

## 8) Networking and egress

- Do not disable TLS verification (`verify=False`). If a certificate
  chain is failing, trust the right CA, don't bypass.
- Outbound calls use a configured timeout — never rely on defaults.
- For Cloud Functions, the Serverless VPC connector + egress rules are
  defined in Terraform; document the required networking in the function's
  README.

## 9) Data classification and retention

- Every Bronze/Silver/Gold dataset is classified: `public`,
  `internal`, `confidential`, `restricted`.
- Retention policy is set at dataset/table level. Default retention for
  Bronze raw data is 90 days unless a legal requirement extends it.
- PII fields are identified in the contract model and tagged for masking
  policies in Silver/Gold. Masking logic lives in SQL/Dataflow, not in
  clients.

## 10) Code review security checklist

Before approving a PR, verify:

- [ ] No secrets introduced, no test values that look like real secrets.
- [ ] All external input goes through a Pydantic contract.
- [ ] SQL uses parameters.
- [ ] New IAM bindings include the least-privilege role (if any).
- [ ] New logs do not include raw payloads or PII.
- [ ] New dependencies pass `pip-audit` and have a justification.
- [ ] Error handling routes permanent failures to DLQ.

## 11) Reporting a vulnerability

Do **not** open a public issue. Follow the process in
[`.github/SECURITY.md`](../../.github/SECURITY.md).

## Related

- [AGENTS.md](../../AGENTS.md)
- [`.github/SECURITY.md`](../../.github/SECURITY.md)
- [cicd.md](../cicd.md)
- [error-handling.md](error-handling.md)
- [coding-style.md](coding-style.md)
