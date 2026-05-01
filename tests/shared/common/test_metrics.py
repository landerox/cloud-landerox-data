"""Unit tests for the Beam metrics helper.

These tests run a minimal DirectRunner pipeline and assert counter values
via :class:`apache_beam.testing.test_pipeline.TestPipeline` + ``MetricsFilter``.
"""

import apache_beam as beam
from apache_beam.metrics.metric import MetricsFilter
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.runners.runner import PipelineResult
from apache_beam.testing.test_pipeline import TestPipeline

from shared.common.metrics import (
    BYTES_READ,
    BYTES_WRITTEN,
    RECORDS_INVALID,
    RECORDS_LATE,
    RECORDS_PROCESSED,
    PipelineMetrics,
    counter,
)

NAMESPACE = "test_pipeline"


class _ObserveAll(beam.DoFn):
    """DoFn that exercises every PipelineMetrics code path per element."""

    def setup(self) -> None:
        self.metrics = PipelineMetrics(NAMESPACE)

    def process(self, element):  # type: ignore[override]
        if element == "valid":
            self.metrics.observe_processed(bytes_in=10, bytes_out=4)
        elif element == "invalid":
            self.metrics.observe_invalid()
        elif element == "late":
            self.metrics.observe_late()
        yield element


def _counter_value(result: PipelineResult, name: str) -> int:
    filt = MetricsFilter().with_namespace(NAMESPACE).with_name(name)
    metrics = result.metrics().query(filt)["counters"]
    assert len(metrics) == 1, f"expected one counter {name}, got {metrics}"
    return metrics[0].committed or metrics[0].attempted


def test_pipeline_metrics_tracks_standard_counters():
    options = PipelineOptions(flags=["--output_table=test:ds.tbl"])
    with TestPipeline(options=options) as pipeline:
        (
            pipeline
            | beam.Create(["valid", "valid", "valid", "invalid", "late"])
            | beam.ParDo(_ObserveAll())
        )
    result = pipeline.result

    assert _counter_value(result, RECORDS_PROCESSED) == 3
    assert _counter_value(result, RECORDS_INVALID) == 1
    assert _counter_value(result, RECORDS_LATE) == 1
    assert _counter_value(result, BYTES_READ) == 30
    assert _counter_value(result, BYTES_WRITTEN) == 12


def test_observe_processed_skips_byte_counters_when_zero():
    metrics = PipelineMetrics("unit-only")
    metrics.observe_processed()
    assert metrics.namespace == "unit-only"


def test_counter_helper_exposes_ad_hoc_counter():
    c = counter("custom", "extra_metric")
    c.inc(2)
