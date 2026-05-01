"""Structured logging utilities for Google Cloud Platform.

Emits JSON records consumable by Cloud Logging. Trace/span identifiers
set via :func:`trace_context` are propagated into every log entry while
the context is active, using the Cloud Logging fields
``logging.googleapis.com/trace`` and ``logging.googleapis.com/spanId``.

For W3C trace propagation across services
(HTTP → Pub/Sub → Dataflow → BigQuery), use :func:`parse_traceparent`
and :func:`trace_context_from_traceparent` at ingress, and
:func:`current_traceparent` to forward the active context downstream.

See ``docs/guides/observability.md`` for the canonical field catalogue.
"""

from collections.abc import Generator
from contextlib import contextmanager
from contextvars import ContextVar
import json
import logging
import re
import sys
from typing import Any

_trace_id_var: ContextVar[str | None] = ContextVar("trace_id", default=None)
_span_id_var: ContextVar[str | None] = ContextVar("span_id", default=None)
_trace_project_var: ContextVar[str | None] = ContextVar("trace_project", default=None)

# W3C Trace Context: version-trace_id-parent_id-trace_flags
# https://www.w3.org/TR/trace-context/#traceparent-header
_TRACEPARENT_RE = re.compile(
    r"^(?P<version>[0-9a-f]{2})-"
    r"(?P<trace_id>[0-9a-f]{32})-"
    r"(?P<span_id>[0-9a-f]{16})-"
    r"(?P<flags>[0-9a-f]{2})$"
)
_INVALID_TRACE_ID = "0" * 32
_INVALID_SPAN_ID = "0" * 16


def parse_traceparent(header: str | None) -> tuple[str, str] | None:
    """Parse a W3C ``traceparent`` header into ``(trace_id, span_id)``.

    Returns ``None`` when the header is missing or malformed -- callers
    should treat that as "no inbound trace context" and either start a
    fresh one or skip ``trace_context`` entirely. Observability helpers
    must never fail user code, so silent rejection is intentional.

    Only W3C version ``00`` is accepted; future versions are ignored
    rather than guessed at. All-zero ids are rejected per the spec.
    """
    if not header:
        return None
    match = _TRACEPARENT_RE.match(header.strip())
    if match is None:
        return None
    if match.group("version") != "00":
        return None
    trace_id = match.group("trace_id")
    span_id = match.group("span_id")
    if trace_id == _INVALID_TRACE_ID or span_id == _INVALID_SPAN_ID:
        return None
    return trace_id, span_id


def build_traceparent(trace_id: str, span_id: str, *, sampled: bool = True) -> str:
    """Format a W3C ``traceparent`` header for outbound propagation.

    ``sampled`` controls the trace-flags byte: ``01`` when sampled,
    ``00`` otherwise. Both ids must already be lowercase hex of the
    correct length; this helper does not pad, normalize, or validate.
    """
    return f"00-{trace_id}-{span_id}-{'01' if sampled else '00'}"


def current_traceparent() -> str | None:
    """Return the active trace context as a W3C ``traceparent`` string.

    Returns ``None`` when no :func:`trace_context` is active or when
    the active context lacks a span id (e.g. set at the request root
    without a span). Use this to forward the trace to outbound calls
    -- Pub/Sub message attributes, downstream HTTP headers, etc.
    """
    trace_id = _trace_id_var.get()
    span_id = _span_id_var.get()
    if not trace_id or not span_id:
        return None
    return build_traceparent(trace_id, span_id)


@contextmanager
def trace_context(
    trace_id: str,
    span_id: str | None = None,
    *,
    project_id: str | None = None,
) -> Generator[None]:
    """Bind trace identifiers to the current execution context.

    While the context is active, every log record formatted by
    :class:`CloudLoggingFormatter` carries the matching Cloud Logging
    trace fields. Nested contexts are safe; previous values are restored
    on exit.

    Args:
        trace_id: Hex trace identifier (typically 32 characters from
            W3C ``traceparent``).
        span_id: Optional hex span identifier. Omit at the request root.
        project_id: GCP project used to build the fully-qualified trace
            resource path ``projects/<id>/traces/<trace_id>`` expected by
            Cloud Logging. If omitted, only the raw trace id is emitted.
    """
    trace_token = _trace_id_var.set(trace_id)
    span_token = _span_id_var.set(span_id)
    project_token = _trace_project_var.set(project_id)
    try:
        yield
    finally:
        _trace_project_var.reset(project_token)
        _span_id_var.reset(span_token)
        _trace_id_var.reset(trace_token)


@contextmanager
def trace_context_from_traceparent(
    header: str | None,
    *,
    project_id: str | None = None,
) -> Generator[None]:
    """Open a :func:`trace_context` from an inbound W3C ``traceparent``.

    Convenience wrapper for ingress points (HTTP request handlers,
    Pub/Sub triggered functions): parses the header, opens a context
    when valid, and otherwise no-ops so the wrapped block always runs.

    Args:
        header: Raw ``traceparent`` value from the inbound request --
            typically ``request.headers.get("traceparent")`` for HTTP
            or ``cloud_event.attributes.get("traceparent")`` for
            Pub/Sub.
        project_id: GCP project used to qualify the trace resource
            path emitted into Cloud Logging.
    """
    parsed = parse_traceparent(header)
    if parsed is None:
        yield
        return
    trace_id, span_id = parsed
    with trace_context(trace_id, span_id=span_id, project_id=project_id):
        yield


class CloudLoggingFormatter(logging.Formatter):
    """JSON formatter for native Cloud Logging integration."""

    def format(self, record: logging.LogRecord) -> str:
        """Converts a LogRecord to a structured JSON string."""
        log_entry: dict[str, Any] = {
            "severity": record.levelname,
            "message": record.getMessage(),
            "timestamp": self.formatTime(record, self.datefmt),
            "logging.googleapis.com/sourceLocation": {
                "file": record.pathname,
                "line": record.lineno,
                "function": record.funcName,
            },
        }

        trace_id = _trace_id_var.get()
        if trace_id:
            project = _trace_project_var.get()
            log_entry["logging.googleapis.com/trace"] = (
                f"projects/{project}/traces/{trace_id}" if project else trace_id
            )
        span_id = _span_id_var.get()
        if span_id:
            log_entry["logging.googleapis.com/spanId"] = span_id

        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        extra_fields = getattr(record, "extra_fields", None)
        if extra_fields:
            log_entry.update(extra_fields)

        return json.dumps(log_entry)


def setup_cloud_logging(level: int = logging.INFO) -> None:
    """Configure the application to emit structured JSON logs.

    Replaces every handler currently attached to the root logger with a
    single ``StreamHandler`` that uses :class:`CloudLoggingFormatter`. This
    is the right behaviour for clean entrypoints (Cloud Functions Gen2
    when invoked outside Functions Framework, Dataflow main scripts, local
    scripts) but is **destructive** when something else has already wired
    a handler.

    Do not call this inside hosts that own logging themselves:

    - **Functions Framework**: it installs its own request-scoped handler
      to flush logs at function exit. Replacing it loses that flush.
    - **Dataflow worker harness**: the worker installs handlers that
      forward to the Dataflow logging service.

    For those hosts, use :func:`attach_cloud_logging_formatter` instead --
    it keeps the existing handlers and only swaps their formatter.

    Args:
        level: Root log level. Defaults to ``logging.INFO``. Override via
            the ``LOG_LEVEL`` env var in production wiring rather than
            hardcoding here.
    """
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(CloudLoggingFormatter())

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    for h in root_logger.handlers[:]:
        root_logger.removeHandler(h)

    root_logger.addHandler(handler)


def attach_cloud_logging_formatter(level: int | None = None) -> None:
    """Apply :class:`CloudLoggingFormatter` to existing root handlers.

    Non-destructive counterpart to :func:`setup_cloud_logging`. Use this
    from hosts that own logging themselves and rely on their handlers to
    flush or forward records:

    - **Functions Framework**: keeps the request-scoped handler that
      flushes logs at function exit.
    - **Dataflow worker harness**: keeps the handler that forwards to the
      Dataflow logging service.

    If the root logger has no handlers (e.g. a bare ``DirectRunner`` run
    or a plain script), this attaches one ``StreamHandler`` to
    ``sys.stdout`` so the call is never a no-op. In that scenario,
    :func:`setup_cloud_logging` is usually the better choice.

    Args:
        level: Optional root log level. Leave ``None`` to keep whatever
            level the host configured.
    """
    formatter = CloudLoggingFormatter()
    root_logger = logging.getLogger()
    if level is not None:
        root_logger.setLevel(level)
    handlers = root_logger.handlers
    if not handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(formatter)
        root_logger.addHandler(handler)
        return
    for h in handlers:
        h.setFormatter(formatter)
