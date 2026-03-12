# Dataflow Pipelines

This directory contains Apache Beam pipelines for Silver/Gold processing.

## Current state

- `pipelines/` is currently a placeholder for runtime modules.
- Runtime pipelines are intentionally kept outside this public baseline.

## Directory layout (recommended at scale)

- `pipelines/`: production pipeline modules (to be added).

Suggested structure for private runtime repos:

```bash
dataflow/pipelines/
└── <domain>/
    ├── bronze/<pipeline_name>/
    │   ├── pipeline.py
    │   ├── metadata.json
    │   ├── requirements.txt
    │   └── README.md
    ├── silver/<pipeline_name>/
    └── gold/<pipeline_name>/
```

## Operating model

This repo supports both processing modes:

- **Streaming** from Pub/Sub for low-latency use cases.
- **Batch** from GCS or scheduled pulls for backfills and periodic processing.

Use a single shared transform path when feasible (Kappa-style). Use separate paths only when constraints require it.

## Storage model

- Default sink: BigQuery native tables (SQL-first delivery).
- Optional sink: BigLake external tables on Parquet/Avro or Iceberg.

## New pipeline skeleton

```bash
pipelines/<domain>/<layer>/<pipeline_name>/
├── pipeline.py
├── metadata.json
├── requirements.txt
└── README.md
```

## Local checks

```bash
just lint
just type
just test
```

For local execution, use DirectRunner and explicit pipeline options.
