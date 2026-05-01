"""Unit tests for shared.common.io helpers."""

from types import SimpleNamespace
from typing import cast
from unittest.mock import patch

import pytest

from shared.common.exceptions import ConfigError
from shared.common.io import BigQueryDisposition, KappaOptions, get_sink, get_source


class _FakeWriteToBigQuery:
    """Test double for WriteToBigQuery."""

    class Method:
        STORAGE_WRITE_API = "STORAGE_WRITE_API"
        FILE_LOADS = "FILE_LOADS"

    def __init__(self, *args: object, **kwargs: object) -> None:
        self.args = args
        self.kwargs = kwargs


def test_get_source_stream_uses_pubsub() -> None:
    options = cast(
        KappaOptions,
        SimpleNamespace(
            input_mode="stream",
            input_subscription="projects/p/subscriptions/s",
            input_path=None,
        ),
    )
    sentinel_source = object()

    with patch(
        "shared.common.io.ReadFromPubSub", return_value=sentinel_source
    ) as mock_pubsub:
        source = get_source(options)

    assert source is sentinel_source
    mock_pubsub.assert_called_once_with(subscription=options.input_subscription)


def test_get_source_stream_requires_subscription() -> None:
    options = cast(
        KappaOptions,
        SimpleNamespace(
            input_mode="stream",
            input_subscription=None,
            input_path=None,
        ),
    )

    with pytest.raises(ConfigError, match="--input_subscription is required"):
        get_source(options)


def test_get_source_batch_uses_gcs_path() -> None:
    options = cast(
        KappaOptions,
        SimpleNamespace(
            input_mode="batch",
            input_subscription=None,
            input_path="gs://bucket/path/*.json",
        ),
    )
    sentinel_source = object()

    with patch(
        "shared.common.io.ReadFromText", return_value=sentinel_source
    ) as mock_read:
        source = get_source(options)

    assert source is sentinel_source
    mock_read.assert_called_once_with(options.input_path)


def test_get_source_batch_requires_input_path() -> None:
    options = cast(
        KappaOptions,
        SimpleNamespace(
            input_mode="batch",
            input_subscription=None,
            input_path=None,
        ),
    )

    with pytest.raises(ConfigError, match="--input_path is required"):
        get_source(options)


def test_get_sink_stream_uses_storage_write_api_and_kms() -> None:
    options = cast(
        KappaOptions,
        SimpleNamespace(
            input_mode="stream",
            output_table="project:dataset.table",
            write_disposition="WRITE_APPEND",
            kms_key="projects/p/locations/us/keyRings/r/cryptoKeys/k",
        ),
    )

    with patch("shared.common.io.WriteToBigQuery", _FakeWriteToBigQuery):
        sink = cast(_FakeWriteToBigQuery, get_sink(options, schema="id:INTEGER"))

    assert sink.args[0] == options.output_table
    assert sink.kwargs["schema"] == "id:INTEGER"
    assert sink.kwargs["method"] == _FakeWriteToBigQuery.Method.STORAGE_WRITE_API
    assert sink.kwargs["create_disposition"] == BigQueryDisposition.CREATE_NEVER
    assert sink.kwargs["write_disposition"] == options.write_disposition
    assert sink.kwargs["use_at_least_once"] is True
    assert sink.kwargs["kms_key"] == options.kms_key


def test_get_sink_defaults_schema_to_none() -> None:
    options = cast(
        KappaOptions,
        SimpleNamespace(
            input_mode="batch",
            output_table="project:dataset.table",
            write_disposition="WRITE_APPEND",
            kms_key=None,
        ),
    )

    with patch("shared.common.io.WriteToBigQuery", _FakeWriteToBigQuery):
        sink = cast(_FakeWriteToBigQuery, get_sink(options))

    assert sink.kwargs["schema"] is None


def test_get_sink_batch_uses_file_loads_and_disables_at_least_once() -> None:
    options = cast(
        KappaOptions,
        SimpleNamespace(
            input_mode="batch",
            output_table="project:dataset.table",
            write_disposition="WRITE_TRUNCATE",
            kms_key=None,
        ),
    )

    with patch("shared.common.io.WriteToBigQuery", _FakeWriteToBigQuery):
        sink = cast(_FakeWriteToBigQuery, get_sink(options))

    assert sink.kwargs["method"] == _FakeWriteToBigQuery.Method.FILE_LOADS
    assert sink.kwargs["use_at_least_once"] is False
    assert sink.kwargs["kms_key"] is None
    assert sink.kwargs["write_disposition"] == "WRITE_TRUNCATE"
