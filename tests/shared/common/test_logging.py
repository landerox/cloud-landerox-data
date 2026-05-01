"""Unit tests for structured logging helpers."""

import json
import logging
import sys

import pytest

from shared.common.logging import (
    CloudLoggingFormatter,
    attach_cloud_logging_formatter,
    build_traceparent,
    current_traceparent,
    parse_traceparent,
    setup_cloud_logging,
    trace_context,
    trace_context_from_traceparent,
)


def _make_record(msg: str = "hello") -> logging.LogRecord:
    return logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname=__file__,
        lineno=10,
        msg=msg,
        args=(),
        exc_info=None,
    )


def test_cloud_logging_formatter_includes_core_fields_and_extra() -> None:
    formatter = CloudLoggingFormatter()
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname=__file__,
        lineno=27,
        msg="hello %s",
        args=("world",),
        exc_info=None,
    )
    record.extra_fields = {"trace_id": "abc-123"}

    log_entry = json.loads(formatter.format(record))

    assert log_entry["severity"] == "INFO"
    assert log_entry["message"] == "hello world"
    assert "timestamp" in log_entry
    assert log_entry["logging.googleapis.com/sourceLocation"]["file"] == __file__
    assert log_entry["logging.googleapis.com/sourceLocation"]["line"] == 27
    assert log_entry["trace_id"] == "abc-123"


def test_cloud_logging_formatter_includes_exception() -> None:
    formatter = CloudLoggingFormatter()

    try:
        raise ValueError("boom")
    except ValueError:
        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname=__file__,
            lineno=51,
            msg="failed",
            args=(),
            exc_info=sys.exc_info(),
        )

    log_entry = json.loads(formatter.format(record))
    assert "exception" in log_entry
    assert "ValueError" in log_entry["exception"]


def test_cloud_logging_formatter_omits_extra_fields_when_not_set() -> None:
    formatter = CloudLoggingFormatter()
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname=__file__,
        lineno=10,
        msg="plain message",
        args=(),
        exc_info=None,
    )

    log_entry = json.loads(formatter.format(record))

    assert "extra_fields" not in log_entry
    assert "trace_id" not in log_entry
    assert log_entry["message"] == "plain message"


def test_cloud_logging_formatter_omits_exception_when_none() -> None:
    formatter = CloudLoggingFormatter()
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname=__file__,
        lineno=10,
        msg="no error",
        args=(),
        exc_info=None,
    )

    log_entry = json.loads(formatter.format(record))

    assert "exception" not in log_entry


def test_trace_context_populates_cloud_logging_fields() -> None:
    formatter = CloudLoggingFormatter()

    with trace_context("abc123", span_id="span-1", project_id="my-proj"):
        entry = json.loads(formatter.format(_make_record()))

    assert entry["logging.googleapis.com/trace"] == "projects/my-proj/traces/abc123"
    assert entry["logging.googleapis.com/spanId"] == "span-1"


def test_trace_context_without_project_emits_raw_trace_id() -> None:
    formatter = CloudLoggingFormatter()

    with trace_context("xyz789"):
        entry = json.loads(formatter.format(_make_record()))

    assert entry["logging.googleapis.com/trace"] == "xyz789"
    assert "logging.googleapis.com/spanId" not in entry


def test_trace_context_cleared_on_exit() -> None:
    formatter = CloudLoggingFormatter()

    with trace_context("abc123", span_id="span-1"):
        pass

    entry = json.loads(formatter.format(_make_record()))
    assert "logging.googleapis.com/trace" not in entry
    assert "logging.googleapis.com/spanId" not in entry


def test_trace_context_nested_restores_outer_on_exit() -> None:
    formatter = CloudLoggingFormatter()

    with trace_context("outer", span_id="s-outer", project_id="p"):
        with trace_context("inner", span_id="s-inner", project_id="p"):
            inner = json.loads(formatter.format(_make_record()))
        outer = json.loads(formatter.format(_make_record()))

    assert inner["logging.googleapis.com/trace"] == "projects/p/traces/inner"
    assert inner["logging.googleapis.com/spanId"] == "s-inner"
    assert outer["logging.googleapis.com/trace"] == "projects/p/traces/outer"
    assert outer["logging.googleapis.com/spanId"] == "s-outer"


def test_setup_cloud_logging_configures_root_logger() -> None:
    root_logger = logging.getLogger()
    original_handlers = root_logger.handlers[:]
    original_level = root_logger.level

    try:
        setup_cloud_logging(level=logging.WARNING)
        assert root_logger.level == logging.WARNING
        assert len(root_logger.handlers) == 1
        assert isinstance(root_logger.handlers[0].formatter, CloudLoggingFormatter)
    finally:
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        for handler in original_handlers:
            root_logger.addHandler(handler)
        root_logger.setLevel(original_level)


# ---------------------------------------------------------------------------
# attach_cloud_logging_formatter
# ---------------------------------------------------------------------------


def test_attach_cloud_logging_formatter_swaps_formatter_on_existing_handlers() -> None:
    root_logger = logging.getLogger()
    original_handlers = root_logger.handlers[:]
    original_level = root_logger.level

    host_handler_a = logging.StreamHandler(sys.stderr)
    host_handler_a.setFormatter(logging.Formatter("%(message)s"))
    host_handler_b = logging.StreamHandler(sys.stderr)
    host_handler_b.setFormatter(logging.Formatter("%(message)s"))

    try:
        for h in root_logger.handlers[:]:
            root_logger.removeHandler(h)
        root_logger.addHandler(host_handler_a)
        root_logger.addHandler(host_handler_b)
        root_logger.setLevel(logging.INFO)

        attach_cloud_logging_formatter()

        assert root_logger.handlers == [host_handler_a, host_handler_b]
        assert isinstance(host_handler_a.formatter, CloudLoggingFormatter)
        assert isinstance(host_handler_b.formatter, CloudLoggingFormatter)
        assert root_logger.level == logging.INFO
    finally:
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        for handler in original_handlers:
            root_logger.addHandler(handler)
        root_logger.setLevel(original_level)


def test_attach_cloud_logging_formatter_sets_level_when_provided() -> None:
    root_logger = logging.getLogger()
    original_handlers = root_logger.handlers[:]
    original_level = root_logger.level

    host_handler = logging.StreamHandler(sys.stderr)
    try:
        for h in root_logger.handlers[:]:
            root_logger.removeHandler(h)
        root_logger.addHandler(host_handler)
        root_logger.setLevel(logging.INFO)

        attach_cloud_logging_formatter(level=logging.DEBUG)

        assert root_logger.level == logging.DEBUG
    finally:
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        for handler in original_handlers:
            root_logger.addHandler(handler)
        root_logger.setLevel(original_level)


def test_attach_cloud_logging_formatter_falls_back_when_no_handlers() -> None:
    root_logger = logging.getLogger()
    original_handlers = root_logger.handlers[:]
    original_level = root_logger.level

    try:
        for h in root_logger.handlers[:]:
            root_logger.removeHandler(h)

        attach_cloud_logging_formatter()

        assert len(root_logger.handlers) == 1
        assert isinstance(root_logger.handlers[0], logging.StreamHandler)
        assert isinstance(root_logger.handlers[0].formatter, CloudLoggingFormatter)
    finally:
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        for handler in original_handlers:
            root_logger.addHandler(handler)
        root_logger.setLevel(original_level)


# ---------------------------------------------------------------------------
# parse_traceparent
# ---------------------------------------------------------------------------


_VALID_TRACE_ID = "0af7651916cd43dd8448eb211c80319c"
_VALID_SPAN_ID = "b7ad6b7169203331"
_VALID_HEADER = f"00-{_VALID_TRACE_ID}-{_VALID_SPAN_ID}-01"


def test_parse_traceparent_returns_ids_for_valid_header() -> None:
    assert parse_traceparent(_VALID_HEADER) == (_VALID_TRACE_ID, _VALID_SPAN_ID)


def test_parse_traceparent_strips_surrounding_whitespace() -> None:
    assert parse_traceparent(f"  {_VALID_HEADER}\n") == (
        _VALID_TRACE_ID,
        _VALID_SPAN_ID,
    )


@pytest.mark.parametrize(
    "header",
    [
        None,
        "",
        "   ",
        # wrong segment count
        "00-abc-def",
        # non-hex characters
        "00-zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz-b7ad6b7169203331-01",
        # wrong trace_id length
        "00-0af7651916cd43dd-b7ad6b7169203331-01",
        # wrong span_id length
        f"00-{_VALID_TRACE_ID}-deadbeef-01",
        # unsupported version
        f"01-{_VALID_TRACE_ID}-{_VALID_SPAN_ID}-01",
        # all-zero trace_id
        f"00-{'0' * 32}-{_VALID_SPAN_ID}-01",
        # all-zero span_id
        f"00-{_VALID_TRACE_ID}-{'0' * 16}-01",
    ],
)
def test_parse_traceparent_returns_none_for_invalid_input(header: str | None) -> None:
    assert parse_traceparent(header) is None


# ---------------------------------------------------------------------------
# build_traceparent
# ---------------------------------------------------------------------------


def test_build_traceparent_emits_sampled_flag_by_default() -> None:
    header = build_traceparent(_VALID_TRACE_ID, _VALID_SPAN_ID)
    assert header == f"00-{_VALID_TRACE_ID}-{_VALID_SPAN_ID}-01"
    # The output must roundtrip through parse_traceparent.
    assert parse_traceparent(header) == (_VALID_TRACE_ID, _VALID_SPAN_ID)


def test_build_traceparent_can_emit_unsampled_flag() -> None:
    header = build_traceparent(_VALID_TRACE_ID, _VALID_SPAN_ID, sampled=False)
    assert header.endswith("-00")


# ---------------------------------------------------------------------------
# current_traceparent
# ---------------------------------------------------------------------------


def test_current_traceparent_returns_none_outside_context() -> None:
    assert current_traceparent() is None


def test_current_traceparent_serializes_active_context() -> None:
    with trace_context(_VALID_TRACE_ID, span_id=_VALID_SPAN_ID, project_id="p"):
        assert current_traceparent() == f"00-{_VALID_TRACE_ID}-{_VALID_SPAN_ID}-01"
    assert current_traceparent() is None


def test_current_traceparent_returns_none_when_span_id_missing() -> None:
    # Root contexts may set only the trace id.
    with trace_context(_VALID_TRACE_ID, span_id=None):
        assert current_traceparent() is None


# ---------------------------------------------------------------------------
# trace_context_from_traceparent
# ---------------------------------------------------------------------------


def test_trace_context_from_traceparent_binds_when_header_valid() -> None:
    formatter = CloudLoggingFormatter()
    with trace_context_from_traceparent(_VALID_HEADER, project_id="proj"):
        entry = json.loads(formatter.format(_make_record()))
    assert (
        entry["logging.googleapis.com/trace"]
        == f"projects/proj/traces/{_VALID_TRACE_ID}"
    )
    assert entry["logging.googleapis.com/spanId"] == _VALID_SPAN_ID


@pytest.mark.parametrize("header", [None, "", "garbage"])
def test_trace_context_from_traceparent_is_noop_for_invalid(header: str | None) -> None:
    formatter = CloudLoggingFormatter()
    with trace_context_from_traceparent(header, project_id="proj"):
        entry = json.loads(formatter.format(_make_record()))
    assert "logging.googleapis.com/trace" not in entry
    assert "logging.googleapis.com/spanId" not in entry


def test_trace_context_from_traceparent_resets_on_exit() -> None:
    with trace_context_from_traceparent(_VALID_HEADER):
        assert current_traceparent() is not None
    assert current_traceparent() is None
