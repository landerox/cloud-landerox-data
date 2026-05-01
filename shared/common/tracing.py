"""OpenTelemetry tracing setup with Cloud Trace export.

Wires :mod:`opentelemetry` to a configured :class:`TracerProvider` whose
spans are exported to Google Cloud Trace via
:class:`opentelemetry.exporter.cloud_trace.CloudTraceSpanExporter`.

The helpers here are deliberately small: callers control the sampler,
the exporter, and the resource so tests inject in-memory variants
without the SDK ever opening a network socket.

Spans started through :func:`start_span` also bind their ``trace_id``
and ``span_id`` to the project-wide ``trace_context`` so every log
record formatted by ``CloudLoggingFormatter`` while the span is active
carries the matching Cloud Logging trace fields. That keeps logs,
metrics, and traces stitched on the same correlation key without an
extra propagator.

See ``docs/guides/observability.md`` for the propagation story (W3C
``traceparent`` ingress, ``trace_context`` correlation into Cloud
Logging, OpenTelemetry spans into Cloud Trace).
"""

from collections.abc import Generator, Mapping
from contextlib import contextmanager

from opentelemetry import trace
from opentelemetry.exporter.cloud_trace import CloudTraceSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import SpanProcessor, TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, SpanExporter
from opentelemetry.sdk.trace.sampling import (
    ParentBased,
    Sampler,
    TraceIdRatioBased,
)
from opentelemetry.trace import Span, Tracer
from opentelemetry.util.types import AttributeValue

from .logging import trace_context

_DEFAULT_SAMPLE_RATIO = 1.0


def setup_tracing(
    *,
    service_name: str,
    project_id: str | None = None,
    sample_ratio: float = _DEFAULT_SAMPLE_RATIO,
    sampler: Sampler | None = None,
    exporter: SpanExporter | None = None,
    processor: SpanProcessor | None = None,
) -> TracerProvider:
    """Install a ``TracerProvider`` that exports spans to Cloud Trace.

    Args:
        service_name: Logical service name; published as the
            ``service.name`` resource attribute and visible in Cloud
            Trace's resource selector.
        project_id: GCP project to export spans to. When ``None``,
            :class:`CloudTraceSpanExporter` falls back to ADC discovery.
            Ignored when ``exporter`` is supplied.
        sample_ratio: Fraction of root traces sampled when no explicit
            ``sampler`` is given. Range ``[0.0, 1.0]``. Default ``1.0``
            keeps the gate open during baseline rollout; tighten per
            pipeline once volume is real.
        sampler: Optional custom sampler. Wins over ``sample_ratio``.
        exporter: Optional custom span exporter. Tests inject an
            in-memory exporter; production callers leave this unset.
        processor: Optional custom span processor. When ``None``, a
            :class:`BatchSpanProcessor` wraps the exporter -- the right
            default for production. Tests typically pass a
            ``SimpleSpanProcessor`` for synchronous flushing.

    Returns:
        The installed ``TracerProvider`` (also retrievable via
        :func:`opentelemetry.trace.get_tracer_provider`). Useful in
        tests to call ``shutdown()`` or to flush a processor.
    """
    selected_sampler = (
        sampler
        if sampler is not None
        else ParentBased(root=TraceIdRatioBased(sample_ratio))
    )
    resource = Resource.create({"service.name": service_name})

    provider = TracerProvider(sampler=selected_sampler, resource=resource)

    selected_exporter = (
        exporter
        if exporter is not None
        else CloudTraceSpanExporter(project_id=project_id)
    )
    selected_processor = (
        processor if processor is not None else BatchSpanProcessor(selected_exporter)
    )
    provider.add_span_processor(selected_processor)

    trace.set_tracer_provider(provider)
    return provider


def get_tracer(name: str) -> Tracer:
    """Return a tracer bound to the current global ``TracerProvider``.

    Thin wrapper over :func:`opentelemetry.trace.get_tracer` so callers
    can import the whole tracing surface from ``shared.common``.
    """
    return trace.get_tracer(name)


@contextmanager
def start_span(
    name: str,
    *,
    tracer: Tracer | None = None,
    attributes: Mapping[str, AttributeValue] | None = None,
    project_id: str | None = None,
) -> Generator[Span]:
    """Start a span and bind its IDs to :func:`trace_context`.

    The span uses the current ``TracerProvider`` configured by
    :func:`setup_tracing`. Its ``trace_id`` and ``span_id`` are also
    bound to the project-wide ``trace_context`` so every log record
    formatted by ``CloudLoggingFormatter`` while the span is active
    carries matching Cloud Logging trace fields. Logs, metrics, and
    traces stitch on the same key without an extra propagator.

    Args:
        name: Span name. Convention: ``<component>.<operation>``,
            e.g. ``ingestion.validate_contract``.
        tracer: Optional tracer override. Falls back to
            ``get_tracer(__name__)``.
        attributes: Optional span attributes to set at start. Use the
            canonical field names from
            ``docs/guides/observability.md`` so traces and logs share
            the same vocabulary.
        project_id: GCP project used to qualify the trace resource
            path in Cloud Logging. Forward the same ``project_id`` you
            passed to :func:`setup_tracing` so logs and traces line up.

    Yields:
        The OpenTelemetry :class:`Span` for the caller to enrich with
        attributes or events.
    """
    active_tracer = tracer if tracer is not None else trace.get_tracer(__name__)
    with active_tracer.start_as_current_span(name, attributes=attributes) as span:
        ctx = span.get_span_context()
        trace_id_hex = format(ctx.trace_id, "032x")
        span_id_hex = format(ctx.span_id, "016x")
        with trace_context(
            trace_id_hex,
            span_id=span_id_hex,
            project_id=project_id,
        ):
            yield span
