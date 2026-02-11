"""
Input/Output utilities for Apache Beam pipelines (Lakehouse/BigLake).

This module provides an abstraction layer for reading from Bronze (GCS/PubSub)
and writing to Silver/Gold layers in BigQuery/BigLake.
"""

import logging
from typing import Any

import apache_beam as beam
from apache_beam.io import ReadFromText
from apache_beam.io.gcp.bigquery import BigQueryDisposition, WriteToBigQuery
from apache_beam.io.gcp.pubsub import ReadFromPubSub
from apache_beam.options.pipeline_options import PipelineOptions


class KappaOptions(PipelineOptions):
    """Custom options for Unified Kappa architecture pipelines."""

    @classmethod
    def _add_argparse_args(cls, parser):
        parser.add_argument(
            "--input_mode",
            default="stream",
            choices=["stream", "batch"],
            help="Execution mode: 'stream' (Pub/Sub) or 'batch' (GCS)",
        )
        parser.add_argument(
            "--input_subscription",
            help="Pub/Sub subscription for streaming mode",
        )
        parser.add_argument(
            "--input_path",
            help="GCS path pattern for batch mode (Bronze Layer)",
        )
        parser.add_argument(
            "--output_table",
            required=True,
            help="BigQuery/BigLake table spec (project:dataset.table)",
        )
        parser.add_argument(
            "--write_disposition",
            default="WRITE_APPEND",
            choices=["WRITE_APPEND", "WRITE_TRUNCATE", "WRITE_EMPTY"],
            help="BigQuery write disposition (APPEND, TRUNCATE, EMPTY)",
        )


def get_source(options: KappaOptions) -> beam.PTransform:
    """
    Factory that returns the appropriate source based on input_mode.
    Supports GCS (Batch) and Pub/Sub (Streaming).
    """
    if options.input_mode == "stream":
        if not options.input_subscription:
            raise ValueError("--input_subscription is required for stream mode")
        logging.info("Reading from Pub/Sub: %s", options.input_subscription)
        return ReadFromPubSub(subscription=options.input_subscription)

    if not options.input_path:
        raise ValueError("--input_path is required for batch mode")
    logging.info("Reading from GCS: %s", options.input_path)
    return ReadFromText(options.input_path)


def get_sink(options: KappaOptions, schema: Any = None) -> beam.PTransform:
    """
    Factory that returns the appropriate BigQuery/BigLake sink.
    Optimizes the write method based on the input mode (Kappa Architecture).
    """
    # Use Storage Write API for low-latency streaming or File Loads for efficient batching.
    method = (
        WriteToBigQuery.Method.STORAGE_WRITE_API
        if options.input_mode == "stream"
        else WriteToBigQuery.Method.FILE_LOADS
    )

    return WriteToBigQuery(
        options.output_table,
        schema=schema,
        method=method,
        create_disposition=BigQueryDisposition.CREATE_NEVER,
        write_disposition=options.write_disposition,
        # Optimal for reliability in Kappa pipelines
        use_at_least_once=(options.input_mode == "stream"),
    )
