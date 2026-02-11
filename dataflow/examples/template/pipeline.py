"""
Dataflow pipeline template for Kappa/Lakehouse architecture.

This module defines a unified pipeline that processes data from Bronze (Pub/Sub or GCS)
and writes to Silver (Iceberg or Standard Parquet/Avro via BigLake).
Includes Dead Letter Queue (DLQ) support and custom metrics.
"""

from collections.abc import Generator
from datetime import UTC, datetime
import json
import logging
import typing
from typing import Any

import apache_beam as beam
from apache_beam.io import WriteToText
from apache_beam.metrics.metric import Metrics
from apache_beam.options.pipeline_options import PipelineOptions, SetupOptions
from apache_beam.pvalue import TaggedOutput

from shared.common import KappaOptions, get_sink, get_source, setup_cloud_logging


class ProcessedData(typing.NamedTuple):
    """Schema for the processed Lakehouse data (Silver Layer)."""

    raw_content: str
    event_timestamp: str  # Original event time for partitioning
    ingested_at: str  # Audit: processing time
    length: int


class TransformData(beam.DoFn):
    """Parses raw input and enriches it with Lakehouse metadata."""

    def __init__(self) -> None:
        super().__init__()
        self.processed_counter = Metrics.counter("silver", "processed")
        self.error_counter = Metrics.counter("silver", "errors")

    def process(
        self, element: str | bytes, *_args: Any, **_kwargs: Any
    ) -> Generator[TaggedOutput | ProcessedData, None, None]:
        """
        Transforms input to uppercase and enriches with metadata.
        Uses TaggedOutput for errors to implement a DLQ pattern.
        """
        try:
            text_content = (
                element.decode("utf-8") if isinstance(element, bytes) else element
            )

            now_iso = datetime.now(UTC).isoformat()
            self.processed_counter.inc()

            yield ProcessedData(
                raw_content=text_content.upper(),
                event_timestamp=now_iso,
                ingested_at=now_iso,
                length=len(text_content),
            )
        except Exception as e:
            self.error_counter.inc()
            logging.error("Failed to process element: %s", str(e))

            yield TaggedOutput(
                "errors",
                {
                    "element": str(element),
                    "error": str(e),
                    "timestamp": datetime.now(UTC).isoformat(),
                },
            )


def run(argv: list[str] | None = None) -> None:
    """Main entry point for the Kappa pipeline."""
    pipeline_options = PipelineOptions(argv)
    kappa_options = pipeline_options.view_as(KappaOptions)
    setup_options = pipeline_options.view_as(SetupOptions)
    setup_options.save_main_session = True

    with beam.Pipeline(options=pipeline_options) as pipeline:
        # 1. READ FROM BRONZE (Source Abstraction)
        raw_data = pipeline | "ReadSource" >> get_source(kappa_options)

        # 2. TRANSFORM (Silver Layer Logic)
        results = raw_data | "Transform" >> beam.ParDo(TransformData()).with_outputs(
            "errors", main="main"
        )

        processed_data = results.main.with_output_types(ProcessedData)
        error_data = results.errors

        # 3. WRITE TO SILVER (Iceberg/BigLake via shared sink)
        _ = (
            processed_data
            | "ToDict" >> beam.Map(lambda x: x._asdict())
            | "WriteSilver" >> get_sink(kappa_options, schema=ProcessedData)
        )

        # 4. WRITE DLQ (Errors to GCS)
        if hasattr(kappa_options, "input_path") and kappa_options.input_path:
            error_path = kappa_options.input_path.replace("source", "errors")
            _ = (
                error_data
                | "FormatError" >> beam.Map(json.dumps)
                | "WriteDLQ" >> WriteToText(error_path, file_name_suffix=".json")
            )


if __name__ == "__main__":
    setup_cloud_logging()
    run()
