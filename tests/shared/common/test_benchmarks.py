"""Micro-benchmarks for shared.common hot paths.

Excluded from the default suite (the `benchmark` marker is filtered out
in `addopts`). Opt in locally with::

    uv run pytest -m benchmark --benchmark-only

These exist to detect performance regressions, not to enforce thresholds
in CI; trends matter more than absolute numbers since they vary across
machines.
"""

from __future__ import annotations

from collections.abc import Callable
import random
from unittest.mock import MagicMock

from pydantic import BaseModel
import pytest
from pytest_benchmark.fixture import BenchmarkFixture

from shared.common.dlq import build_dlq_payload
from shared.common.exceptions import TransientError
from shared.common.logging import (
    build_traceparent,
    current_traceparent,
    parse_traceparent,
    trace_context,
)
from shared.common.retry import retry
from shared.common.validation import validate_contract

pytestmark = pytest.mark.benchmark


# -----------------------------------------------------------------------------
# validate_contract
# -----------------------------------------------------------------------------


class _Sample(BaseModel):
    id: int
    name: str
    value: float
    flag: bool


def test_validate_contract_simple(benchmark: BenchmarkFixture) -> None:
    payload = {"id": 1, "name": "alice", "value": 3.14, "flag": True}
    result = benchmark(validate_contract, payload, _Sample)
    assert result.id == 1


# -----------------------------------------------------------------------------
# traceparent
# -----------------------------------------------------------------------------


_VALID_HEADER = "00-0af7651916cd43dd8448eb211c80319c-b7ad6b7169203331-01"
_VALID_TRACE = "0af7651916cd43dd8448eb211c80319c"
_VALID_SPAN = "b7ad6b7169203331"


def test_parse_traceparent_valid(benchmark: BenchmarkFixture) -> None:
    benchmark(parse_traceparent, _VALID_HEADER)


def test_build_traceparent(benchmark: BenchmarkFixture) -> None:
    benchmark(build_traceparent, _VALID_TRACE, _VALID_SPAN)


def test_current_traceparent_inside_context(benchmark: BenchmarkFixture) -> None:
    with trace_context(_VALID_TRACE, span_id=_VALID_SPAN, project_id="p"):
        benchmark(current_traceparent)


# -----------------------------------------------------------------------------
# DLQ payload
# -----------------------------------------------------------------------------


def test_build_dlq_payload(benchmark: BenchmarkFixture) -> None:
    benchmark(
        build_dlq_payload,
        source="payments_webhook",
        schema_version="v1",
        reason_code="schema_invalid",
        error_details="missing field 'amount'",
        payload={"id": "abc", "raw": "x" * 200},
    )


def test_dlq_payload_to_json_bytes(benchmark: BenchmarkFixture) -> None:
    payload = build_dlq_payload(
        source="s",
        schema_version="v1",
        reason_code="r",
        error_details="e",
        payload={"k": "v" * 50},
    )
    benchmark(payload.to_json_bytes)


# -----------------------------------------------------------------------------
# retry happy path
# -----------------------------------------------------------------------------


def test_retry_no_failures(benchmark: BenchmarkFixture) -> None:
    sleeper = MagicMock()
    decorated = retry(sleeper=sleeper, rng=random.Random(0))(lambda: 42)
    benchmark(decorated)
    sleeper.assert_not_called()


def test_retry_one_transient_then_success(benchmark: BenchmarkFixture) -> None:
    sleeper = MagicMock()

    def make_function() -> Callable[[], int]:
        attempts = {"n": 0}

        @retry(base_delay=0.0, sleeper=sleeper, rng=random.Random(0))
        def func() -> int:
            attempts["n"] += 1
            if attempts["n"] == 1:
                raise TransientError("once")
            return 42

        return func

    # Lambda is required: each round must rebuild the closure so the
    # attempt counter resets and the retry path actually fires.
    benchmark(lambda: make_function()())  # noqa: PLW0108
