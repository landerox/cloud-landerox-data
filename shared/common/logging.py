"""
Structured logging utilities for Google Cloud Platform.

This module provides a JSON formatter compatible with Cloud Logging,
enabling advanced observability and filtering in the GCP Console.
"""

import json
import logging
import sys
from typing import Any


class CloudLoggingFormatter(logging.Formatter):
    """
    Formats Python log records as JSON objects for native Cloud Logging integration.
    """

    def format(self, record: logging.LogRecord) -> str:
        """Converts a LogRecord to a structured JSON string."""
        log_entry: dict[str, Any] = {
            "severity": record.levelname,
            "message": record.getMessage(),
            "timestamp": self.formatTime(record, self.datefmt),
            "logging.googleapis.com/sourceLocation": {
                "file": record.pathname,
                "line": record.lineno,
                "function": record.funcName,
            },
        }

        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        # Merge additional metadata if provided via 'extra={"extra_fields": {...}}'
        extra_fields = getattr(record, "extra_fields", None)
        if extra_fields:
            log_entry.update(extra_fields)

        return json.dumps(log_entry)


def setup_cloud_logging(level: int = logging.INFO) -> None:
    """
    Configures the application to use structured JSON logging.
    """
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(CloudLoggingFormatter())

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Clean up existing handlers to prevent duplicate entries
    for h in root_logger.handlers[:]:
        root_logger.removeHandler(h)

    root_logger.addHandler(handler)
