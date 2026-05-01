# Observability Guide

Logging, metrics, tracing, and SLO conventions for this repository.

Logging, metrics, W3C trace-propagation primitives, **and** the
OpenTelemetry → Cloud Trace export wiring ship today in
`shared/common/{logging.py,metrics.py,tracing.py}`. Spans started
via `start_span` automatically bind their IDs to the
`trace_context`, so Cloud Logging trace fields and Cloud Trace spans
share the same correlation key without an extra propagator.

## 1) Pillars

- **Logs** — structured JSON, shipped automatically to Cloud Logging.
- **Metrics** — Beam counters via `shared.common.PipelineMetrics` and
  Cloud Monitoring custom metrics.
- **Traces** — `trace_id`/`span_id` flow into log entries via
  `trace_context`; W3C `traceparent` ingress and egress are wired with
  `parse_traceparent` / `trace_context_from_traceparent` /
  `current_traceparent`. OpenTelemetry spans exported to Cloud Trace
  via `setup_tracing` + `start_span` (see §3.4).
- **SLOs** — per-pipeline/per-function, tracked on Cloud Monitoring.

No component reads any of these three pillars in isolation. Dashboards
join them through a shared correlation key (`trace_id` / `event_id`).

## 2) Logging

### 2.1 Setup

Two helpers, picked by host:

- `shared.common.setup_cloud_logging()` -- replaces every handler on the
  root logger with a single `StreamHandler` formatted as JSON. Right for
  clean entrypoints (Cloud Functions Gen2 outside Functions Framework,
  Dataflow main scripts, local scripts).
- `shared.common.attach_cloud_logging_formatter()` -- non-destructive
  variant that keeps the host's handlers and only swaps their formatter.
  Required when the host owns logging:
  - **Functions Framework** installs a request-scoped handler that
    flushes logs at function exit. `setup_cloud_logging` removes it.
  - **Dataflow worker harness** installs handlers that forward to the
    Dataflow logging service. Same caveat.

```python
from shared.common import setup_cloud_logging

setup_cloud_logging()
```

```python
# Inside a Functions Framework or Dataflow worker entrypoint:
from shared.common import attach_cloud_logging_formatter

attach_cloud_logging_formatter()
```

Both helpers install `CloudLoggingFormatter`, which emits each record
as a JSON object with the fields Cloud Logging indexes natively.

### 2.2 Levels

| Level | Use for |
| :--- | :--- |
| `DEBUG` | Development only. Never emitted in production. |
| `INFO` | Normal lifecycle events (pipeline started, batch processed). |
| `WARNING` | Unexpected but recoverable (retryable error, missing optional field). |
| `ERROR` | Failure that needs attention (DLQ routing, permanent error). |
| `CRITICAL` | System-level failure (startup misconfig, auth rejected). |

Production default is `INFO`. Set `LOG_LEVEL` to override; never hardcode.

### 2.3 Structured context

Pass structured fields via `extra={"extra_fields": {...}}`:

```python
logging.info(
    "event processed",
    extra={
        "extra_fields": {
            "source": "payments_webhook",
            "schema_version": "v1",
            "event_id": event_id,
            "duration_ms": elapsed_ms,
        }
    },
)
```

Canonical field names (use these instead of inventing new ones):

| Field | Type | Meaning |
| :--- | :--- | :--- |
| `source` | string | Logical origin (`<domain>_<source>_<mode>`). |
| `event_id` | string | Stable per-event identifier. |
| `schema_version` | string | Contract version in play (`v1`, `v2`). |
| `reason_code` | string | DLQ/error category (see [error-handling.md](error-handling.md)). |
| `duration_ms` | number | Elapsed time for the logged operation. |
| `record_count` | number | Size of a batch or page. |
| `layer` | string | `bronze` / `silver` / `gold`. |
| `pipeline` | string | Pipeline or function module name. |
| `environment` | string | `dev` / `stg` / `prd`. |

### 2.4 What not to log

- Full payloads, unless behind a debug flag and PII-safe. See
  [security.md](security.md).
- Secrets, signed URLs, tokens, or authorization headers.
- Stack traces for *expected* outcomes (e.g. a contract rejection is a
  `WARNING`/`ERROR` with fields, not a raw traceback).

## 3) Trace and span IDs

To correlate logs across Function → Pub/Sub → Dataflow → BigQuery:

- `shared.common.trace_context` binds `trace_id`, `span_id`, and an
  optional `project_id` to a `ContextVar`. Every log record formatted
  by `CloudLoggingFormatter` while the context is active carries
  `logging.googleapis.com/trace` as
  `projects/<project-id>/traces/<trace_id>` and
  `logging.googleapis.com/spanId` so Cloud Logging stitches entries
  automatically.
- `shared.common.parse_traceparent(header)` and
  `shared.common.trace_context_from_traceparent(header, *, project_id)`
  open the context from a W3C `traceparent` header. Invalid or missing
  headers are silent no-ops -- observability helpers must never fail
  user code.
- `shared.common.current_traceparent()` serializes the active context
  back into a `traceparent` string for outbound propagation
  (Pub/Sub message attributes, downstream HTTP).
- `shared.common.publish_to_pubsub_dlq` already auto-injects the
  active `traceparent` into the published message attributes so DLQ
  subscribers can stitch the dead-letter back to the originating
  request.

### 3.1 Ingress shape (HTTP function)

```python
from shared.common import (
    setup_cloud_logging,
    trace_context_from_traceparent,
)

setup_cloud_logging()

def main(request):
    with trace_context_from_traceparent(
        request.headers.get("traceparent"),
        project_id=PROJECT_ID,
    ):
        ...  # all logs here carry trace + span fields
```

### 3.2 Ingress shape (Pub/Sub triggered)

```python
from shared.common import (
    setup_cloud_logging,
    trace_context_from_traceparent,
)

setup_cloud_logging()

def main(cloud_event):
    header = (cloud_event.attributes or {}).get("traceparent")
    with trace_context_from_traceparent(header, project_id=PROJECT_ID):
        ...
```

### 3.3 Egress propagation (manual publish)

```python
from shared.common import current_traceparent

attrs = {}
tp = current_traceparent()
if tp:
    attrs["traceparent"] = tp
publisher.publish(topic_path, body, **attrs)
```

### 3.4 OpenTelemetry spans into Cloud Trace

`shared.common.setup_tracing` installs a `TracerProvider` whose spans
export to Cloud Trace through `CloudTraceSpanExporter`, batched by
`BatchSpanProcessor`. Call it once per entrypoint:

```python
from shared.common import setup_tracing

setup_tracing(
    service_name="payments_webhook",
    project_id="my-project",
    sample_ratio=1.0,  # tighten per pipeline once volume is real
)
```

Open spans with `start_span`. The helper binds the span's ``trace_id``
and ``span_id`` to ``trace_context`` for the duration of the block,
so logs and traces share the same correlation key:

```python
from shared.common import start_span

with start_span("ingestion.validate_contract", project_id="my-project") as span:
    span.set_attribute("source", "payments_webhook")
    span.set_attribute("schema_version", "v1")
    event = validate_contract(payload, PaymentEventV1)
```

`setup_tracing` is fully injectable for tests: pass an
`InMemorySpanExporter` and a `SimpleSpanProcessor` to assert on
exported spans without opening a network socket.

## 4) Metrics

### 4.1 Beam pipeline metrics (standard)

Every pipeline exposes these counters at minimum:

| Counter | Scope | Meaning |
| :--- | :--- | :--- |
| `records_processed` | per layer | Input records that completed processing. |
| `records_invalid` | per layer | Records routed to DLQ. |
| `records_late` | streaming only | Records arriving after the allowed lateness. |
| `bytes_read` | source | Input byte volume. |
| `bytes_written` | sink | Output byte volume. |

`shared.common.PipelineMetrics` exposes these via
`beam.metrics.Metrics.counter("<namespace>", "<name>")` under a
pipeline-owned namespace. Pipelines instantiate it once per `DoFn` and
do not invent their own counter names. Use
`shared.common.metrics.counter` only for pipeline-specific counters that
fall outside the canonical set.

### 4.2 Cloud Monitoring custom metrics

Runtime modules can emit custom metrics under the
`custom.googleapis.com/cloud-landerox-data/<pipeline>/<metric>` namespace.
Publish them from the pipeline, not from the shared library.

### 4.3 Infrastructure metrics

Provided automatically by GCP and not configured here:

- Cloud Functions: invocations, execution time, errors.
- Dataflow: system lag, data watermark, element throughput, worker count.
- BigQuery: job duration, slot usage, bytes processed.
- Pub/Sub: subscription backlog age and size.

Alerting thresholds on these are defined in the Terraform repo.

## 5) SLOs

Each runtime module declares an SLO in its README using this template:

| Dimension | Target | Window | Notes |
| :--- | :--- | :--- | :--- |
| **Availability** | 99.5% | rolling 28 d | Fraction of minutes without ingestion errors. |
| **Latency (streaming)** | p95 ≤ 60 s | rolling 7 d | Event time → Silver visibility. |
| **Freshness (batch)** | ≤ 1 h after scheduled | rolling 7 d | From run completion to Gold table visible. |
| **Error rate** | ≤ 0.1% | rolling 28 d | DLQ size / total processed. |

Numbers are defaults; each pipeline tightens or relaxes them with
justification.

Error budget is burned by DLQ records and by failed runs. When the budget
for a window is exhausted, new non-critical work for that pipeline is
paused until the budget recovers.

## 6) Dashboards

Each domain has at least one dashboard covering:

- Ingestion rate (events/s) per source.
- DLQ size and DLQ rate per pipeline.
- End-to-end latency (p50/p95/p99) per pipeline.
- Freshness (now − latest event time) per layer.
- Error budget burn for the SLO window.

Dashboards are provisioned via Terraform and exported as JSON alongside
the runtime code.

## 7) Alerting

Alert on:

- DLQ growth above a threshold over 15 min.
- Freshness older than 2× the SLO target for 3 consecutive checks.
- Error rate above the SLO target for 10 min.
- Pub/Sub subscription backlog age > SLO target.
- Workflow failures on any backfill / replay job.

Alerts are page-worthy only when they imply user impact or irrecoverable
state. Low-severity alerts go to ticketing, not on-call.

## 8) Local observability

- Logs in the devcontainer print as JSON to stdout; pipe through `jq`
  while iterating.
- Pub/Sub emulator (`just emulator-pubsub`) does not produce Cloud
  Monitoring metrics; use counters printed from Beam
  `DirectRunner` runs.

## 9) Commands reference

```bash
# Tail logs from a deployed function (example; requires gcloud auth)
gcloud functions logs read <function-name> --region=<region> --limit=50

# Inspect Dataflow job metrics
gcloud dataflow jobs describe <job-id> --region=<region>
```

## Related

- [AGENTS.md](../../AGENTS.md)
- [architecture.md](../architecture.md) — Observability + SLO is a minimum pattern
- [error-handling.md](error-handling.md)
- [coding-style.md](coding-style.md) — logging usage rules
- [security.md](security.md) — redaction and PII rules
