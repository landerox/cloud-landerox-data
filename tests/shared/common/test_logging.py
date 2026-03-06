"""Unit tests for structured logging helpers."""

import json
import logging
import sys

from shared.common.logging import CloudLoggingFormatter, setup_cloud_logging


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
