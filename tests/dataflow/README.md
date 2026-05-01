# Dataflow Tests

Placeholder mirroring `dataflow/pipelines/`.

## Status

This folder is **intentionally empty in this public baseline.** Tests
for production pipelines live alongside the runtime code in private
runtime repositories.

## Layout

Mirror the runtime source tree exactly:

```text
dataflow/pipelines/<domain>/<layer>/<pipeline_name>/pipeline.py
  -> tests/dataflow/<domain>/<layer>/<pipeline_name>/test_pipeline.py
```

## Standards

- Use the `beam_test_pipeline` fixture from
  [`tests/conftest.py`](../conftest.py) (wraps
  `apache_beam.testing.test_pipeline.TestPipeline`).
- Assert with `apache_beam.testing.util.assert_that` plus the matchers
  in `apache_beam.testing.util`.
- Cover at minimum: parsing, contract validation, DLQ side output,
  windowing (when streaming), and sink schema compatibility. See
  [docs/guides/testing.md §6](../../docs/guides/testing.md#6-apache-beam-tests).
- Mark heavyweight end-to-end tests with `@pytest.mark.slow` so they
  run nightly only. The `nightly.yml` workflow picks them up via
  `pytest -m "integration or slow"`.

## Where to look next

- [tests/README.md](../README.md) — fixtures and run commands.
- [docs/guides/testing.md](../../docs/guides/testing.md) — test categories and quality bars.
- [docs/guides/dataflow.md](../../docs/guides/dataflow.md) — engineering standards.
- [dataflow/pipelines/README.md](../../dataflow/pipelines/README.md) — runtime layout.
