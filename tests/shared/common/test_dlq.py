"""Unit tests for DLQ helpers. All GCP clients are mocked."""

from datetime import UTC, datetime
import json
from unittest.mock import MagicMock

import pytest

from shared.common.dlq import (
    DLQPayload,
    build_dlq_payload,
    load_dlq_payload,
    publish_to_pubsub_dlq,
    write_to_gcs_dlq,
)
from shared.common.exceptions import SinkWriteError
from shared.common.logging import trace_context


def _payload() -> DLQPayload:
    return build_dlq_payload(
        source="payments_webhook",
        schema_version="v1",
        reason_code="schema_invalid",
        error_details="missing field 'amount'",
        payload={"id": "abc", "raw": "..."},
        event_id="evt-1",
        event_time=datetime(2026, 4, 22, 12, 0, tzinfo=UTC),
    )


def test_build_dlq_payload_fills_defaults():
    payload = build_dlq_payload(
        source="s",
        schema_version="v1",
        reason_code="schema_invalid",
        error_details="oops",
        payload={"k": "v"},
    )
    assert payload.event_id
    assert payload.event_time.tzinfo is not None


def test_dlq_payload_to_json_bytes_roundtrip():
    payload = _payload()
    body = payload.to_json_bytes()
    assert isinstance(body, bytes)
    decoded = json.loads(body.decode("utf-8"))
    assert decoded["event_id"] == "evt-1"
    assert decoded["reason_code"] == "schema_invalid"


def test_load_dlq_payload_parses_bytes_and_str():
    payload = _payload()
    body = payload.to_json_bytes()
    assert load_dlq_payload(body) == payload
    assert load_dlq_payload(body.decode("utf-8")) == payload


def test_dlq_payload_forbids_extra_fields():
    with pytest.raises(ValueError):
        DLQPayload.model_validate(
            {
                "event_id": "x",
                "event_time": "2026-04-22T00:00:00Z",
                "source": "s",
                "schema_version": "v1",
                "reason_code": "r",
                "error_details": "e",
                "payload": {},
                "rogue": "no",
            }
        )


def test_publish_to_pubsub_dlq_sends_message_and_merged_attributes():
    publisher = MagicMock()
    publisher.topic_path.return_value = "projects/p/topics/t"
    future = MagicMock()
    future.result.return_value = "msg-1"
    publisher.publish.return_value = future

    msg_id = publish_to_pubsub_dlq(
        project_id="p",
        topic_id="t",
        payload=_payload(),
        attributes={"extra": "attr", "source": "overridden-by-payload"},
        publisher=publisher,
    )

    assert msg_id == "msg-1"
    args, kwargs = publisher.publish.call_args
    assert args[0] == "projects/p/topics/t"
    assert json.loads(args[1].decode("utf-8"))["event_id"] == "evt-1"
    assert kwargs["reason_code"] == "schema_invalid"
    assert kwargs["source"] == "overridden-by-payload"
    assert kwargs["extra"] == "attr"


def test_publish_to_pubsub_dlq_injects_active_traceparent():
    publisher = MagicMock()
    publisher.topic_path.return_value = "projects/p/topics/t"
    future = MagicMock()
    future.result.return_value = "msg-1"
    publisher.publish.return_value = future

    trace_id = "0af7651916cd43dd8448eb211c80319c"
    span_id = "b7ad6b7169203331"
    with trace_context(trace_id, span_id=span_id, project_id="proj"):
        publish_to_pubsub_dlq(
            project_id="p",
            topic_id="t",
            payload=_payload(),
            publisher=publisher,
        )

    _, kwargs = publisher.publish.call_args
    assert kwargs["traceparent"] == f"00-{trace_id}-{span_id}-01"


def test_publish_to_pubsub_dlq_explicit_traceparent_overrides_inflight():
    publisher = MagicMock()
    publisher.topic_path.return_value = "projects/p/topics/t"
    future = MagicMock()
    future.result.return_value = "msg-1"
    publisher.publish.return_value = future

    explicit = f"00-{'a' * 32}-{'b' * 16}-00"
    with trace_context("0" * 31 + "1", span_id="0" * 15 + "2"):
        publish_to_pubsub_dlq(
            project_id="p",
            topic_id="t",
            payload=_payload(),
            attributes={"traceparent": explicit},
            publisher=publisher,
        )

    _, kwargs = publisher.publish.call_args
    assert kwargs["traceparent"] == explicit


def test_publish_to_pubsub_dlq_omits_traceparent_when_no_context():
    publisher = MagicMock()
    publisher.topic_path.return_value = "projects/p/topics/t"
    future = MagicMock()
    future.result.return_value = "msg-1"
    publisher.publish.return_value = future

    publish_to_pubsub_dlq(
        project_id="p",
        topic_id="t",
        payload=_payload(),
        publisher=publisher,
    )

    _, kwargs = publisher.publish.call_args
    assert "traceparent" not in kwargs


def test_publish_to_pubsub_dlq_wraps_failure_in_sink_write_error():
    publisher = MagicMock()
    publisher.topic_path.return_value = "projects/p/topics/t"
    publisher.publish.side_effect = RuntimeError("network down")

    with pytest.raises(SinkWriteError) as exc_info:
        publish_to_pubsub_dlq(
            project_id="p",
            topic_id="t",
            payload=_payload(),
            publisher=publisher,
        )
    assert isinstance(exc_info.value.__cause__, RuntimeError)


def test_write_to_gcs_dlq_uses_partitioned_path_and_uploads_json():
    client = MagicMock()
    bucket = MagicMock()
    blob = MagicMock()
    client.bucket.return_value = bucket
    bucket.blob.return_value = blob

    fixed_now = datetime(2026, 4, 22, 10, 30, tzinfo=UTC)
    uri = write_to_gcs_dlq(
        bucket="my-dlq",
        prefix="payments/webhook/",
        payload=_payload(),
        client=client,
        now=fixed_now,
    )

    client.bucket.assert_called_once_with("my-dlq")
    object_name = bucket.blob.call_args.args[0]
    assert object_name.startswith("payments/webhook/2026/04/22/evt-1-")
    assert object_name.endswith(".json")
    assert uri == f"gs://my-dlq/{object_name}"

    upload_kwargs = blob.upload_from_string.call_args
    body = upload_kwargs.args[0]
    assert json.loads(body.decode("utf-8"))["event_id"] == "evt-1"
    assert upload_kwargs.kwargs["content_type"] == "application/json"


def test_write_to_gcs_dlq_wraps_failure_in_sink_write_error():
    client = MagicMock()
    bucket = MagicMock()
    blob = MagicMock()
    client.bucket.return_value = bucket
    bucket.blob.return_value = blob
    blob.upload_from_string.side_effect = RuntimeError("gcs unavailable")

    with pytest.raises(SinkWriteError) as exc_info:
        write_to_gcs_dlq(
            bucket="b",
            prefix="p",
            payload=_payload(),
            client=client,
        )
    assert isinstance(exc_info.value.__cause__, RuntimeError)
