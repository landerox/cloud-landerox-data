# Runtime Templates (Baseline)

These templates are starter artifacts for private runtime repositories.

## Files

- `contracts/source_events_v1.schema.json`: baseline contract template.
- `config/config.template.json`: baseline runtime configuration template.

## Usage

1. Copy templates into your private runtime repository.
2. Rename and adapt values to your domain/source context.
3. Keep secrets and environment values outside git (Secret Manager, CI variables).
4. Validate template changes in CI (`just lint`, `just type`, `just test`).

## Scope

Templates in this public repository are reference-only. Production rollout,
IAM/KMS enforcement, and environment deployment belong to runtime/infra repos.
