# Error Handling Guide

How errors are raised, propagated, logged, and recovered across this repo.

The exception hierarchy (`shared/common/exceptions.py`), the DLQ helpers
(`shared/common/dlq.py`), and the retry decorator
(`shared/common/retry.py`) implement this guide today. Runtime repos
inherit them via `pip install` of the shared package.

## 1) Principles

1. **Fail loudly at boundaries, gracefully inside.**
   - At system boundaries (ingestion handlers, pipeline entrypoints),
     translate unexpected errors into structured logs + DLQ routing.
   - Inside helpers, raise typed exceptions. Do not swallow and return `None`.
2. **Type your failures.** Use the project exception hierarchy (below).
   Never raise bare `Exception` or `ValueError` for domain conditions.
3. **Log with context.** Every error log must include enough structured
   fields (`source`, `event_id`, `schema_version`, `reason_code`) to be
   triaged from the Cloud Logging UI without reading code.
4. **Never lose the original error.** Always chain with `raise X from err`.
5. **No bare `except:` or `except Exception:`** without (a) a narrow
   reason, (b) logging, and (c) re-raising or routing.

## 2) Exception hierarchy

Implemented in `shared/common/exceptions.py`:

```text
CloudLanderoxError              (base; all project errors inherit)
├── ConfigError                 (missing / invalid configuration)
│   └── SecretNotFoundError
├── ContractError               (input validation / schema)
│   ├── ContractValidationError
│   └── SchemaIncompatibleError
├── PipelineIOError             (renamed from IOError to avoid shadowing the builtin)
│   ├── SourceReadError
│   └── SinkWriteError
├── TransientError              (retry-eligible)
│   └── ExternalServiceError
└── PermanentError              (do not retry; route to DLQ)
    └── PoisonMessageError
```

Rules:

- Library code raises the most specific subclass available.
- Handlers catch at the **category** level (`TransientError`,
  `PermanentError`, `ContractError`) and decide retry vs DLQ.
- Every exception carries a short `reason_code` string suitable for DLQ
  tagging (e.g. `"schema_invalid"`, `"sink_write_failed"`).

### 2.1 Reason code catalogue

These strings are the stable contract for DLQ tags, dashboard filters,
and structured logs. Add new codes only by extending the hierarchy in
`shared/common/exceptions.py`; never inline literals at call sites.

| Exception | `reason_code` |
| :--- | :--- |
| `CloudLanderoxError` | `unknown_error` |
| `ConfigError` | `config_missing` |
| `SecretNotFoundError` | `secret_not_found` |
| `ContractError` | `contract_error` |
| `ContractValidationError` | `schema_invalid` |
| `SchemaIncompatibleError` | `schema_incompatible` |
| `PipelineIOError` | `pipeline_io_error` |
| `SourceReadError` | `source_read_failed` |
| `SinkWriteError` | `sink_write_failed` |
| `TransientError` | `transient` |
| `ExternalServiceError` | `external_service_transient` |
| `PermanentError` | `permanent` |
| `PoisonMessageError` | `poison_message` |

The catalogue is enforced by `tests/test_doc_coherence.py`: a code that
exists in `exceptions.py` but is missing from this table fails CI.

## 3) Raise vs return `None`

- **New code:** raise a typed exception. `None` as a failure signal is
  forbidden in new public APIs.
- **`validate_contract`:** raises `ContractValidationError` on failure
  (with the underlying ``pydantic.ValidationError`` chained via ``__cause__``).
  The boundary handler decides DLQ routing.

## 4) Retry and backoff

- Retry only `TransientError` / `ExternalServiceError`.
- Use **exponential backoff with jitter**. Bound by attempts **and** total
  wall time.
- Do not implement ad-hoc retry loops; use the shared
  `@shared.common.retry` decorator so policy stays consistent. It
  injects `sleeper`/`clock`/`rng` for deterministic tests.
- Idempotency keys are mandatory for any operation retried at a distance
  (Pub/Sub → Function → BigQuery).

Illustrative policy (subject to per-service tuning):

| Layer | Attempts | Max elapsed | Base delay |
| :--- | :--- | :--- | :--- |
| HTTP client to third-party API | 5 | 30 s | 0.5 s |
| GCP client (Secret Manager, BigQuery) | 3 | 10 s | 0.2 s |
| Pub/Sub publish | 4 | 20 s | 0.5 s |

## 5) Logging an error

Always include structured context. Do not format the payload into the
message string.

```python
import logging

logging.error(
    "contract validation failed",
    extra={
        "extra_fields": {
            "source": "payments_webhook",
            "schema_version": "v1",
            "event_id": event_id,
            "reason_code": "schema_invalid",
            "errors": exc.errors(),
        }
    },
)
```

`CloudLoggingFormatter` (see `shared/common/logging.py`) turns these into
JSON consumable by Cloud Logging filters.

## 6) Chaining

Preserve the original traceback:

```python
try:
    client.access_secret_version(request={"name": name})
except GoogleAPICallError as err:
    raise SecretNotFoundError(
        f"secret {secret_id} not accessible in {project}"
    ) from err
```

Do not use `raise X from None` unless the upstream error is genuinely
irrelevant (rare).

## 7) Dead-letter queue (DLQ) routing

Every ingestion surface and every Dataflow pipeline must have a DLQ path.

- **Functions:** on `PermanentError` / `ContractError`, publish the
  original payload plus error metadata to the domain's DLQ topic.
- **Dataflow:** route invalid records through a side output into a DLQ
  table/topic. Never drop silently.
- **Payload shape (minimum):**

  ```json
  {
    "event_id": "...",
    "event_time": "2026-04-22T12:34:56Z",
    "source": "payments_webhook",
    "schema_version": "v1",
    "reason_code": "schema_invalid",
    "error_details": "...",
    "payload": { "...": "original record..." }
  }
  ```

- **Reason codes** are stable strings, chosen from a documented
  enumeration. Add new codes in a PR, never inline.

## 8) Idempotency

- Consumer handlers must tolerate at-least-once delivery.
- Keying strategy: use the source's natural `event_id` when available;
  derive deterministically otherwise (hash of immutable fields).
- Deduplication window must be explicit per pipeline (BigQuery merge key,
  Beam keyed state with TTL, or application-level table lookup).

## 9) At the boundary

A typical HTTP ingestion handler:

```python
def main(request):
    try:
        payload = request.get_json()
        event = validate_contract(payload, PaymentEventV1)  # raises on fail
        publish_to_pubsub(event)
    except ContractError as err:
        route_to_dlq(payload, reason_code=err.reason_code, error_details=str(err))
        return ("", 202)  # accepted, but won't be processed
    except TransientError:
        return ("retry", 503)  # upstream will retry
    except CloudLanderoxError as err:
        logging.exception("unhandled project error", extra={...})
        return ("", 500)
```

## 10) Anti-patterns

- `except Exception: pass` — forbidden.
- `except Exception as e: logging.error(e)` — forbidden; log with context
  and re-raise or route to DLQ.
- Catching `BaseException` — forbidden.
- Returning tuples like `(result, error)` — use exceptions or
  `Result`-style types (only if a dedicated helper is introduced
  project-wide).
- Magic strings for error categories — use exception types and
  `reason_code` constants.

## Related

- [AGENTS.md](../../AGENTS.md)
- [architecture.md](../architecture.md) — DLQ + replay sit in Minimum patterns
- [coding-style.md](coding-style.md)
- [observability.md](observability.md)
