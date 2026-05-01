"""Standard Apache Beam metrics for pipelines.

Exposes the five canonical counters documented in
``docs/guides/observability.md`` §4.1 so pipelines report them with
consistent names and namespaces. Pipelines use :class:`PipelineMetrics`
instead of calling :func:`apache_beam.metrics.Metrics.counter` directly,
which keeps counter names from drifting across modules.
"""

from apache_beam.metrics.metric import Metrics

RECORDS_PROCESSED = "records_processed"
RECORDS_INVALID = "records_invalid"
RECORDS_LATE = "records_late"
BYTES_READ = "bytes_read"
BYTES_WRITTEN = "bytes_written"


class PipelineMetrics:
    """Canonical counters for a pipeline, namespaced by pipeline name.

    Instances are cheap: the underlying :class:`beam.metrics.Metrics.counter`
    objects lazily register themselves with the Beam runner. Instantiate
    once per ``DoFn`` and reuse across the ``process`` method.
    """

    __slots__ = (
        "bytes_read",
        "bytes_written",
        "namespace",
        "records_invalid",
        "records_late",
        "records_processed",
    )

    def __init__(self, namespace: str) -> None:
        """Create counters under ``namespace`` (typically the pipeline name)."""
        self.namespace = namespace
        self.records_processed = Metrics.counter(namespace, RECORDS_PROCESSED)
        self.records_invalid = Metrics.counter(namespace, RECORDS_INVALID)
        self.records_late = Metrics.counter(namespace, RECORDS_LATE)
        self.bytes_read = Metrics.counter(namespace, BYTES_READ)
        self.bytes_written = Metrics.counter(namespace, BYTES_WRITTEN)

    def observe_processed(self, bytes_in: int = 0, bytes_out: int = 0) -> None:
        """Record one successfully processed record and its byte volume."""
        self.records_processed.inc(1)
        if bytes_in:
            self.bytes_read.inc(bytes_in)
        if bytes_out:
            self.bytes_written.inc(bytes_out)

    def observe_invalid(self) -> None:
        """Record one record routed to DLQ."""
        self.records_invalid.inc(1)

    def observe_late(self) -> None:
        """Record one record arriving after allowed lateness (streaming only)."""
        self.records_late.inc(1)


def counter(namespace: str, name: str) -> Metrics.DelegatingCounter:
    """Create an ad-hoc counter for pipeline-specific metrics.

    Use this only when a counter does not fit the canonical set above.
    Pipeline-specific counters still live under the pipeline's namespace
    so dashboards can aggregate by namespace.
    """
    return Metrics.counter(namespace, name)
