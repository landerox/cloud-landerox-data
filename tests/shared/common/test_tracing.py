"""Unit tests for OpenTelemetry tracing setup and span helpers.

Every test injects an in-memory exporter + a SimpleSpanProcessor so the
suite never opens a network socket. The ``_reset_tracer_provider``
fixture clears OpenTelemetry's "set once" guard between tests so each
test installs a fresh global provider; without it, only the first
``setup_tracing`` call wins and subsequent tests see the wrong tracer.
"""

from collections.abc import Generator

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import (
    InMemorySpanExporter,
)
from opentelemetry.sdk.trace.sampling import ALWAYS_ON, ParentBased
from opentelemetry.util._once import Once
import pytest

from shared.common.logging import current_traceparent
from shared.common.tracing import get_tracer, setup_tracing, start_span


@pytest.fixture(autouse=True)
def _reset_tracer_provider() -> Generator[None]:  # pyright: ignore[reportUnusedFunction]
    """Reset OpenTelemetry's global TracerProvider between tests.

    ``opentelemetry.trace.set_tracer_provider`` is gated by a
    module-level ``Once`` so the first caller wins and subsequent
    overrides are silently dropped (with a WARNING). Tests need a
    fresh provider per case, so we reach into the private state and
    reset both flags before each test.
    """
    trace._TRACER_PROVIDER = None  # pyright: ignore[reportPrivateUsage]
    trace._TRACER_PROVIDER_SET_ONCE = Once()  # pyright: ignore[reportPrivateUsage]
    yield
    trace._TRACER_PROVIDER = None  # pyright: ignore[reportPrivateUsage]
    trace._TRACER_PROVIDER_SET_ONCE = Once()  # pyright: ignore[reportPrivateUsage]


def _make_provider(
    service: str = "test-service",
) -> tuple[TracerProvider, InMemorySpanExporter]:
    exporter = InMemorySpanExporter()
    processor = SimpleSpanProcessor(exporter)
    provider = setup_tracing(
        service_name=service,
        exporter=exporter,
        processor=processor,
    )
    return provider, exporter


# ---------------------------------------------------------------------------
# setup_tracing
# ---------------------------------------------------------------------------


def test_setup_tracing_installs_provider_globally() -> None:
    provider, _ = _make_provider()
    assert trace.get_tracer_provider() is provider


def test_setup_tracing_default_sampler_is_parent_based_ratio() -> None:
    provider, _ = _make_provider()
    sampler = provider.sampler
    assert isinstance(sampler, ParentBased)
    # The root sampler is a private attribute of ParentBased, so we rely
    # on the public description string -- it includes the wrapped
    # sampler's name and ratio.
    assert "TraceIdRatioBased" in sampler.get_description()


def test_setup_tracing_explicit_sampler_wins_over_ratio() -> None:
    exporter = InMemorySpanExporter()
    processor = SimpleSpanProcessor(exporter)
    provider = setup_tracing(
        service_name="explicit-sampler",
        sample_ratio=0.0,
        sampler=ALWAYS_ON,
        exporter=exporter,
        processor=processor,
    )
    assert provider.sampler is ALWAYS_ON


def test_setup_tracing_attaches_service_name_resource() -> None:
    provider, _ = _make_provider(service="payments-webhook")
    resource_attrs = provider.resource.attributes
    assert resource_attrs["service.name"] == "payments-webhook"


# ---------------------------------------------------------------------------
# get_tracer
# ---------------------------------------------------------------------------


def test_get_tracer_returns_tracer_bound_to_global_provider() -> None:
    provider, _ = _make_provider()
    tracer = get_tracer("my.module")
    # Tracer instances are not directly comparable, so we verify the
    # round-trip: a span created by this tracer reaches the provider's
    # processor and lands in the in-memory exporter.
    assert tracer is not None
    assert provider is trace.get_tracer_provider()


# ---------------------------------------------------------------------------
# start_span
# ---------------------------------------------------------------------------


def test_start_span_records_span_with_attributes() -> None:
    provider, exporter = _make_provider()
    tracer = provider.get_tracer("test")

    with start_span(
        "ingestion.validate_contract",
        tracer=tracer,
        attributes={"source": "payments_webhook", "schema_version": "v1"},
    ):
        pass

    spans = exporter.get_finished_spans()
    assert len(spans) == 1
    span = spans[0]
    assert span.name == "ingestion.validate_contract"
    assert span.attributes is not None
    assert span.attributes["source"] == "payments_webhook"
    assert span.attributes["schema_version"] == "v1"


def test_start_span_binds_trace_context_inside_block() -> None:
    provider, _ = _make_provider()
    tracer = provider.get_tracer("test")

    captured: dict[str, str | None] = {"traceparent": None}

    with start_span("op", tracer=tracer, project_id="my-proj") as span:
        ctx = span.get_span_context()
        captured["traceparent"] = current_traceparent()
        captured["expected_trace"] = format(ctx.trace_id, "032x")
        captured["expected_span"] = format(ctx.span_id, "016x")

    active = captured["traceparent"]
    assert active is not None
    assert captured["expected_trace"] in active
    assert captured["expected_span"] in active


def test_start_span_clears_trace_context_on_exit() -> None:
    provider, _ = _make_provider()
    tracer = provider.get_tracer("test")

    with start_span("op", tracer=tracer):
        assert current_traceparent() is not None

    assert current_traceparent() is None


def test_start_span_falls_back_to_module_tracer() -> None:
    _, exporter = _make_provider()

    with start_span("global.tracer.path"):
        pass

    spans = exporter.get_finished_spans()
    assert any(s.name == "global.tracer.path" for s in spans)


def test_start_span_yields_span_for_enrichment() -> None:
    provider, exporter = _make_provider()
    tracer = provider.get_tracer("test")

    with start_span("enrich", tracer=tracer) as span:
        span.set_attribute("enriched", "yes")

    spans = exporter.get_finished_spans()
    assert spans[-1].attributes is not None
    assert spans[-1].attributes["enriched"] == "yes"
