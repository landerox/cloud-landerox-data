"""Shared common utilities for the cloud-landerox-data project."""

import importlib.metadata

from .dlq import (
    DLQPayload,
    build_dlq_payload,
    load_dlq_payload,
    publish_to_pubsub_dlq,
    write_to_gcs_dlq,
)
from .exceptions import (
    CloudLanderoxError,
    ConfigError,
    ContractError,
    ContractValidationError,
    ExternalServiceError,
    PermanentError,
    PipelineIOError,
    PoisonMessageError,
    SchemaIncompatibleError,
    SecretNotFoundError,
    SinkWriteError,
    SourceReadError,
    TransientError,
)
from .io import KappaOptions, get_sink, get_source
from .logging import (
    attach_cloud_logging_formatter,
    build_traceparent,
    current_traceparent,
    parse_traceparent,
    setup_cloud_logging,
    trace_context,
    trace_context_from_traceparent,
)
from .metrics import PipelineMetrics
from .retry import retry
from .secrets import get_secret
from .tracing import get_tracer, setup_tracing, start_span
from .validation import validate_contract

try:
    __version__ = importlib.metadata.version("cloud-landerox-data")
except importlib.metadata.PackageNotFoundError:
    __version__ = "unknown"

__all__ = [
    "CloudLanderoxError",
    "ConfigError",
    "ContractError",
    "ContractValidationError",
    "DLQPayload",
    "ExternalServiceError",
    "KappaOptions",
    "PermanentError",
    "PipelineIOError",
    "PipelineMetrics",
    "PoisonMessageError",
    "SchemaIncompatibleError",
    "SecretNotFoundError",
    "SinkWriteError",
    "SourceReadError",
    "TransientError",
    "__version__",
    "attach_cloud_logging_formatter",
    "build_dlq_payload",
    "build_traceparent",
    "current_traceparent",
    "get_secret",
    "get_sink",
    "get_source",
    "get_tracer",
    "load_dlq_payload",
    "parse_traceparent",
    "publish_to_pubsub_dlq",
    "retry",
    "setup_cloud_logging",
    "setup_tracing",
    "start_span",
    "trace_context",
    "trace_context_from_traceparent",
    "validate_contract",
    "write_to_gcs_dlq",
]
