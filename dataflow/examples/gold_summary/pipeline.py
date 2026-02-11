"""
Dataflow pipeline example for the Gold Layer (Heavy Aggregation).

This pipeline performs complex business aggregations that require the
distributed processing power of Dataflow (ETL pattern), complementing
SQL-based transformations in Dataform.
"""

import typing

import apache_beam as beam
from apache_beam.io.gcp.bigquery import ReadFromBigQuery
from apache_beam.options.pipeline_options import PipelineOptions

from shared.common import KappaOptions, get_sink, setup_cloud_logging


class GoldSummary(typing.NamedTuple):
    """Schema for business-ready aggregates."""

    date: str
    total_events: int
    avg_length: float


def run(argv: list[str] | None = None) -> None:
    """Main entry point for Gold pipeline."""
    options = PipelineOptions(argv)
    kappa_options = options.view_as(KappaOptions)

    with beam.Pipeline(options=options) as pipeline:
        # 1. READ FROM SILVER (BigQuery)
        silver_data = pipeline | "ReadSilver" >> ReadFromBigQuery(
            table=kappa_options.output_table.replace(
                "enriched", "silver"
            ),  # Dummy logic
            use_standard_sql=True,
        )

        # 2. AGGREGATE (Business Logic)
        gold_data = (
            silver_data
            | "ExtractDate"
            >> beam.Map(lambda x: (x["event_timestamp"][:10], x["length"]))
            | "GroupAndSum" >> beam.CombinePerKey(sum)
            | "FormatGold"
            >> beam.Map(
                lambda x: GoldSummary(date=x[0], total_events=1, avg_length=float(x[1]))
            )
        )

        # 3. WRITE TO GOLD
        _ = (
            gold_data
            | "ToDict" >> beam.Map(lambda x: x._asdict())
            | "WriteGold" >> get_sink(kappa_options, schema=GoldSummary)
        )


if __name__ == "__main__":
    setup_cloud_logging()
    run()
