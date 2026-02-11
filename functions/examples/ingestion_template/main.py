"""
Example Ingestion Cloud Function (Bronze Layer).

This function serves as a template for pulling data from an external API
and landing it in Cloud Storage using the Lakehouse multi-format strategy.
"""

from datetime import UTC, datetime
import json
import logging
import typing
from typing import Any

from flask import Request, Response
import functions_framework

from shared.common import setup_cloud_logging

# Setup structured logging for Cloud Logging
setup_cloud_logging()
logger = logging.getLogger(__name__)


class RawEvent(typing.NamedTuple):
    """Schema for the raw event data (Bronze Layer)."""

    id: str
    data: dict[str, Any]
    received_at: str


@functions_framework.http
def main(request: Request) -> Response:
    """
    HTTP entry point for the ingestion function.
    Validates input, parses to a typed structure, and prepares for GCS landing.
    """
    try:
        request_json = request.get_json(silent=True)

        if not request_json:
            return Response("No data received", status=400)

        # 1. Parse into a typed structure (Static analysis via 'ty')
        event = RawEvent(
            id=str(request_json.get("id", "unknown")),
            data=request_json,
            received_at=datetime.now(UTC).isoformat(),
        )

        # 2. Log processing (Structured metadata)
        logger.info(
            "Processing ingestion event", extra={"extra_fields": {"event_id": event.id}}
        )

        # 3. Bronze Landing (GCS or Pub/Sub)
        # - For Pattern A (Archival): Use GCS client to save as NDJSON/Avro/Parquet.
        # - For Pattern B (Async): Publish the event to a Pub/Sub topic for direct BQ ingestion.
        # Format and landing choice based on source characteristics.

        return Response(
            json.dumps({"status": "success", "event_id": event.id}),
            status=200,
            mimetype="application/json",
        )

    except Exception:
        logger.exception("Failed to process ingestion")
        return Response("Internal Error", status=500)
