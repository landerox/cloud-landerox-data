"""Dead-letter queue (DLQ) routing helpers.

Implements the canonical DLQ payload shape documented in
``docs/guides/error-handling.md`` §7. Callers build a
:class:`DLQPayload` once and publish it to either a Pub/Sub topic
(streaming pipelines and functions) or a GCS prefix (batch/offline
archival).

Both sinks are thin wrappers: authentication and retry behaviour come
from the underlying GCP clients and :mod:`shared.common.retry`
respectively. Clients are injectable so tests never touch the network.
"""

from collections.abc import Mapping
from datetime import UTC, datetime
import json
import logging
import uuid

from google.cloud import pubsub_v1, storage
from pydantic import BaseModel, ConfigDict, Field

from .exceptions import SinkWriteError
from .logging import current_traceparent


class DLQPayload(BaseModel):
    """Canonical shape for a dead-lettered record."""

    model_config = ConfigDict(extra="forbid")

    event_id: str
    event_time: datetime
    source: str
    schema_version: str
    reason_code: str
    error_details: str
    payload: dict[str, object] = Field(default_factory=dict)

    def to_json_bytes(self) -> bytes:
        """Serialize to the UTF-8 JSON bytes expected by Pub/Sub/GCS."""
        return self.model_dump_json().encode("utf-8")


def publish_to_pubsub_dlq(
    *,
    project_id: str,
    topic_id: str,
    payload: DLQPayload,
    attributes: Mapping[str, str] | None = None,
    publisher: pubsub_v1.PublisherClient | None = None,
) -> str:
    """Publish a DLQ payload to a Pub/Sub topic.

    Args:
        project_id: GCP project hosting the DLQ topic.
        topic_id: Topic short name (no ``projects/.../topics/`` prefix).
        payload: Canonical DLQ payload.
        attributes: Optional Pub/Sub message attributes. ``reason_code``,
            ``source``, and ``schema_version`` are always injected so
            subscribers can filter without decoding the message body.
        publisher: Optional pre-configured publisher client. Tests inject
            a fake; production callers rely on the default client.

    Returns:
        The Pub/Sub message id assigned by the server.

    Raises:
        SinkWriteError: Publish failed; the original client error is
            chained via ``__cause__``.
    """
    client = publisher if publisher is not None else pubsub_v1.PublisherClient()
    topic_path = client.topic_path(project_id, topic_id)

    merged_attrs: dict[str, str] = {
        "reason_code": payload.reason_code,
        "source": payload.source,
        "schema_version": payload.schema_version,
    }
    # Forward the active trace context so DLQ subscribers can stitch the
    # dead-letter back to the originating request. No-op when no
    # trace_context is active. User-supplied attributes still win.
    inflight = current_traceparent()
    if inflight is not None:
        merged_attrs["traceparent"] = inflight
    if attributes:
        merged_attrs.update(attributes)

    try:
        future = client.publish(topic_path, payload.to_json_bytes(), **merged_attrs)
        message_id = future.result()
    except Exception as err:
        # Catch-all on purpose: pubsub_v1 raises a non-uniform mix
        # (GoogleAPICallError, RetryError, RuntimeError on closed
        # publishers, transport-level errors via gRPC) and the contract
        # of this helper is "any publish failure becomes SinkWriteError
        # with __cause__ preserved". Narrowing the catch would silently
        # leak some of those classes to callers.
        logging.error(
            "dlq pubsub publish failed",
            extra={
                "extra_fields": {
                    "reason_code": SinkWriteError.reason_code,
                    "topic": topic_path,
                    "event_id": payload.event_id,
                }
            },
        )
        raise SinkWriteError(f"failed to publish DLQ payload to {topic_path}") from err

    logging.info(
        "dlq pubsub publish ok",
        extra={
            "extra_fields": {
                "topic": topic_path,
                "event_id": payload.event_id,
                "message_id": message_id,
                "reason_code": payload.reason_code,
            }
        },
    )
    return message_id


def write_to_gcs_dlq(
    *,
    bucket: str,
    prefix: str,
    payload: DLQPayload,
    client: storage.Client | None = None,
    now: datetime | None = None,
) -> str:
    """Write a DLQ payload as a JSON object in GCS.

    Objects are stored under
    ``<prefix>/<YYYY>/<MM>/<DD>/<event_id>-<uuid>.json`` so hive-style
    partitioning works without an explicit partition column.

    Args:
        bucket: Destination bucket name.
        prefix: Path prefix inside the bucket (no leading ``/``).
        payload: Canonical DLQ payload.
        client: Optional pre-configured GCS client. Tests inject a fake.
        now: Optional timestamp for partitioning. Defaults to ``utcnow``.

    Returns:
        The ``gs://`` URI of the object written.

    Raises:
        SinkWriteError: Write failed; the original client error is
            chained via ``__cause__``.
    """
    storage_client = client if client is not None else storage.Client()
    when = now if now is not None else datetime.now(UTC)
    object_name = (
        f"{prefix.rstrip('/')}/{when:%Y/%m/%d}/"
        f"{payload.event_id}-{uuid.uuid4().hex}.json"
    )
    uri = f"gs://{bucket}/{object_name}"

    try:
        blob = storage_client.bucket(bucket).blob(object_name)
        blob.upload_from_string(
            payload.to_json_bytes(),
            content_type="application/json",
        )
    except Exception as err:
        # Catch-all on purpose: google-cloud-storage raises a non-uniform
        # mix (GoogleAPICallError subclasses, ClientError, transport-level
        # errors). The contract of this helper is "any write failure
        # becomes SinkWriteError with __cause__ preserved", and narrowing
        # the catch would silently leak some of those classes to callers.
        logging.error(
            "dlq gcs write failed",
            extra={
                "extra_fields": {
                    "reason_code": SinkWriteError.reason_code,
                    "uri": uri,
                    "event_id": payload.event_id,
                }
            },
        )
        raise SinkWriteError(f"failed to write DLQ payload to {uri}") from err

    logging.info(
        "dlq gcs write ok",
        extra={
            "extra_fields": {
                "uri": uri,
                "event_id": payload.event_id,
                "reason_code": payload.reason_code,
            }
        },
    )
    return uri


def build_dlq_payload(
    *,
    source: str,
    schema_version: str,
    reason_code: str,
    error_details: str,
    payload: Mapping[str, object],
    event_id: str | None = None,
    event_time: datetime | None = None,
) -> DLQPayload:
    """Convenience builder that fills optional fields with sane defaults."""
    return DLQPayload(
        event_id=event_id or uuid.uuid4().hex,
        event_time=event_time or datetime.now(UTC),
        source=source,
        schema_version=schema_version,
        reason_code=reason_code,
        error_details=error_details,
        payload=dict(payload),
    )


def load_dlq_payload(raw: bytes | str) -> DLQPayload:
    """Parse a JSON-encoded DLQ message (e.g. the body of a Pub/Sub
    message or a GCS blob). Useful for replay tooling."""
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8")
    return DLQPayload.model_validate(json.loads(raw))
