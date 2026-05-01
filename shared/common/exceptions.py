"""Project exception hierarchy.

Implements the hierarchy described in ``docs/guides/error-handling.md``.

Every exception carries a class-level ``reason_code``: a short, stable
string suitable for DLQ tagging and dashboard filters. Reason codes do
not change across releases; add new codes in a PR, never inline.
"""

from typing import ClassVar


class CloudLanderoxError(Exception):
    """Base class for all project-level exceptions."""

    reason_code: ClassVar[str] = "unknown_error"


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------


class ConfigError(CloudLanderoxError):
    """Required configuration is missing or invalid."""

    reason_code: ClassVar[str] = "config_missing"


class SecretNotFoundError(ConfigError):
    """A Secret Manager lookup failed or the secret is not accessible."""

    reason_code: ClassVar[str] = "secret_not_found"


# ---------------------------------------------------------------------------
# Contract / schema
# ---------------------------------------------------------------------------


class ContractError(CloudLanderoxError):
    """Payload does not satisfy the declared contract or schema."""

    reason_code: ClassVar[str] = "contract_error"


class ContractValidationError(ContractError):
    """Payload failed Pydantic validation against its contract class."""

    reason_code: ClassVar[str] = "schema_invalid"


class SchemaIncompatibleError(ContractError):
    """Declared schema version is not compatible with the consumer."""

    reason_code: ClassVar[str] = "schema_incompatible"


# ---------------------------------------------------------------------------
# I/O
# ---------------------------------------------------------------------------


class PipelineIOError(CloudLanderoxError):
    """Base for pipeline read/write failures.

    Named ``PipelineIOError`` rather than ``IOError`` to avoid shadowing
    the built-in ``IOError`` at import time. Catch the specific subclass
    (``SourceReadError`` / ``SinkWriteError``) whenever possible.
    """

    reason_code: ClassVar[str] = "pipeline_io_error"


class SourceReadError(PipelineIOError):
    """Reading from a pipeline source failed."""

    reason_code: ClassVar[str] = "source_read_failed"


class SinkWriteError(PipelineIOError):
    """Writing to a pipeline sink failed."""

    reason_code: ClassVar[str] = "sink_write_failed"


# ---------------------------------------------------------------------------
# Retry semantics
# ---------------------------------------------------------------------------


class TransientError(CloudLanderoxError):
    """A transient condition; handlers should retry with backoff."""

    reason_code: ClassVar[str] = "transient"


class ExternalServiceError(TransientError):
    """An external service returned a retryable error (5xx, 429, timeout)."""

    reason_code: ClassVar[str] = "external_service_transient"


class PermanentError(CloudLanderoxError):
    """A permanent failure; handlers must not retry and should route to DLQ."""

    reason_code: ClassVar[str] = "permanent"


class PoisonMessageError(PermanentError):
    """A message that cannot be processed regardless of retries."""

    reason_code: ClassVar[str] = "poison_message"
