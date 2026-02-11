"""
Unit tests for the template Dataflow pipeline.
"""

import logging
import unittest

import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.testing.test_pipeline import TestPipeline
from apache_beam.testing.util import assert_that, equal_to

# Import the transform to test
from dataflow.examples.template.pipeline import TransformData


class TestTemplatePipeline(unittest.TestCase):
    """Test suite for business logic in the Dataflow template."""

    def test_transform_logic(self):
        """
        Verifies that the business logic (Upper case + length) works as expected.
        """
        inputs = ["hello world", "kappa architecture"]
        expected_outputs = [
            {"raw_content": "HELLO WORLD", "length": 11},
            {"raw_content": "KAPPA ARCHITECTURE", "length": 18},
        ]

        # Explicitly use DirectRunner
        options = PipelineOptions(
            [
                "--output_table=dummy:dataset.table",
                "--input_mode=batch",
                "--input_path=dummy",
                "--runner=DirectRunner",
            ]
        )

        with TestPipeline(options=options) as p:
            input_pcoll = p | beam.Create(inputs)

            output_pcoll = (
                input_pcoll
                | beam.ParDo(TransformData())
                # Convert NamedTuple to dict for assertion comparison
                | beam.Map(lambda x: {"raw_content": x.raw_content, "length": x.length})
            )

            assert_that(output_pcoll, equal_to(expected_outputs))

    def test_bytes_handling(self):
        """
        Verifies it handles bytes (like from PubSub) correctly.
        """
        inputs = [b"binary data"]
        expected_outputs = [{"raw_content": "BINARY DATA", "length": 11}]

        options = PipelineOptions(
            [
                "--output_table=dummy:dataset.table",
                "--input_mode=batch",
                "--input_path=dummy",
                "--runner=DirectRunner",
            ]
        )

        with TestPipeline(options=options) as p:
            input_pcoll = p | beam.Create(inputs)

            output_pcoll = (
                input_pcoll
                | beam.ParDo(TransformData())
                # Convert NamedTuple to dict for assertion comparison
                | beam.Map(lambda x: {"raw_content": x.raw_content, "length": x.length})
            )

            assert_that(output_pcoll, equal_to(expected_outputs))


if __name__ == "__main__":
    logging.getLogger().setLevel(logging.INFO)
    unittest.main()
