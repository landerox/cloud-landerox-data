# Testing Guide

Test strategy, layout, and quality bars for this repository.

`tests/README.md` describes the physical structure. This guide defines
**how we test and what we expect to pass**.

## 1) Test categories

Every test belongs to exactly one of these categories, selected via
pytest markers:

| Marker | Scope | Allowed dependencies | Runs in |
| :--- | :--- | :--- | :--- |
| `unit` (default) | A single function/class. No I/O. | Mocked GCP/HTTP. | Every PR. |
| `integration` | Multiple components or emulators. | Pub/Sub / BigQuery emulators, local filesystem. | Nightly and on demand. |
| `slow` | Expensive setup, large fixtures, Beam end-to-end. | Same as above. | Nightly. |

Markers are declared in `pyproject.toml` under
`[tool.pytest.ini_options].markers` and enforced by `--strict-markers`.

Run subsets:

```bash
uv run pytest -m "unit"
uv run pytest -m "integration and not slow"
uv run pytest -m "slow"
```

## 2) Mocking policy

- **Never hit real GCP services, HTTP endpoints, or databases** in any
  category of test. Integration tests use local emulators or fakes.
- Reuse the mocks in [`tests/conftest.py`](../../tests/conftest.py) before
  introducing new ones:
  - `mock_storage_client`, `mock_gcs_file_content`
  - `mock_bigquery_client`, `mock_bq_query_results`
  - `mock_secret_manager`, `mock_secret_value`
  - `mock_http_request`, `mock_cloud_event`
  - `mock_requests`, `mock_api_response`
  - `beam_test_pipeline`
- Fixtures live in `tests/conftest.py`. Module-local fixtures may live in
  the nearest `conftest.py` next to the test file.

## 3) Layout

Mirror the source tree exactly:

```text
shared/common/io.py           ->  tests/shared/common/test_io.py
functions/ingestion/<...>/main.py ->  tests/functions/<...>/test_main.py
dataflow/pipelines/<...>/pipeline.py ->  tests/dataflow/<...>/test_pipeline.py
```

Test file naming: `test_<module>.py`. Test function naming: `test_<behavior>`
in snake_case, preferably stating the expected outcome
(`test_get_sink_batch_uses_file_loads_and_disables_at_least_once`).

## 4) Structure of a test

- Use **Arrange / Act / Assert** sections separated by a blank line.
- One logical assertion per test. Multiple `assert` lines are fine when
  they describe the same outcome.
- Avoid `unittest.TestCase`-style classes; use functions and parametrize.

Example:

```python
def test_validate_contract_success() -> None:
    data = {"id": 1, "name": "Ada"}

    result = validate_contract(data, User)

    assert result is not None
    assert result.id == 1
```

## 5) Parametrization

Use `pytest.mark.parametrize` instead of loops:

```python
@pytest.mark.parametrize(
    ("mode", "expected_method"),
    [
        ("stream", "STORAGE_WRITE_API"),
        ("batch", "FILE_LOADS"),
    ],
)
def test_get_sink_method(mode, expected_method): ...
```

## 6) Apache Beam tests

- Use `apache_beam.testing.test_pipeline.TestPipeline` from the
  `beam_test_pipeline` fixture.
- Assert outputs with `apache_beam.testing.util.assert_that` and matchers.
- Cover at minimum: parsing, contract validation, DLQ path, windowing if
  applicable.

## 7) Time, randomness, and the outside world

- **Time:** freeze with `freezegun` (fixture `freeze_time`). Never call
  `datetime.now()` inside tests without freezing.
- **Randomness:** seed with `random.seed(0)` or use deterministic inputs.
- **Filesystem:** use the `tmp_path` fixture. Do not write to the repo tree.
- **Environment variables:** set via the `monkeypatch` fixture. The
  autouse `set_test_environment` fixture already provides safe defaults
  for `GOOGLE_CLOUD_PROJECT`, `GCP_PROJECT`, and `FUNCTION_REGION`.

## 8) Coverage

- Tool: `pytest-cov` (declared in the `dev` dependency group).
- Target: **90% minimum** line + branch coverage for `shared/common/**`,
  enforced by `[tool.coverage.report].fail_under = 90` in
  `pyproject.toml`. Actual coverage sits near 100%; the gate exists to
  catch regressions, not to set the bar.
- Runtime modules (`functions/**`, `dataflow/pipelines/**`) set their own
  coverage target in their module README; the floor is 70%.
- CI fails the PR if coverage drops below the target.

Local run:

```bash
uv run pytest --cov=shared --cov-report=term-missing
```

## 9) What to test

Every module must cover:

1. **Happy path** — the feature works as documented.
2. **Contract violations** — invalid input is rejected the expected way
   (return `None`, raise a typed error, route to DLQ).
3. **Boundary cases** — empty input, missing env vars, both branches of any
   `if` on a public argument.
4. **Failure modes** — third-party client raises, credentials are missing.

## 10) What NOT to test

- Third-party libraries themselves. Trust Apache Beam, Pydantic, google-cloud-*.
- Private helpers when a public test already covers the path.
- Log message formatting beyond "did we emit a log line at the right level
  with the right context key".

## 11) Flakiness policy

Flaky tests are **bugs**. Do not `@pytest.mark.flaky` or quarantine without
a tracking issue. Fix the root cause:

- Non-deterministic ordering → sort before asserting.
- Time-dependent behavior → freeze time.
- Emulator race conditions → add explicit sync points, never `sleep`.

## 12) Commands reference

```bash
just test                              # full suite, mirrors CI
uv run pytest -m "unit"                # fast inner loop
uv run pytest tests/shared/common/test_io.py::test_get_sink_defaults_schema_to_none
uv run pytest --cov=shared --cov-fail-under=80
```

## Related

- [AGENTS.md](../../AGENTS.md)
- [coding-style.md](coding-style.md)
- [error-handling.md](error-handling.md)
- [`tests/README.md`](../../tests/README.md)
- [`tests/conftest.py`](../../tests/conftest.py)
