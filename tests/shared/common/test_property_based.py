"""Property-based tests for shared.common with Hypothesis.

These complement the example-based tests by checking invariants over
generated input. They are intentionally narrow: no GCP, no network, no
sleeping (sleeper is mocked everywhere). Each strategy is sized so the
suite stays under the default pytest timeout.
"""

from __future__ import annotations

import random
from unittest.mock import MagicMock

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from pydantic import BaseModel
import pytest

from shared.common.exceptions import TransientError
from shared.common.logging import build_traceparent, parse_traceparent
from shared.common.retry import retry
from shared.common.validation import ContractValidationError, validate_contract

# =============================================================================
# Strategies
# =============================================================================

_HEX = "0123456789abcdef"
_TRACE_ID = st.text(alphabet=_HEX, min_size=32, max_size=32).filter(
    lambda s: s != "0" * 32
)
_SPAN_ID = st.text(alphabet=_HEX, min_size=16, max_size=16).filter(
    lambda s: s != "0" * 16
)


# =============================================================================
# retry — behavioural invariants
# =============================================================================


@given(
    n_failures=st.integers(min_value=0, max_value=5),
    spare_attempts=st.integers(min_value=1, max_value=4),
)
@settings(max_examples=40, deadline=None)
def test_retry_succeeds_when_attempts_outnumber_failures(
    n_failures: int, spare_attempts: int
) -> None:
    """If transient errors happen <max_attempts times, the call still returns."""
    max_attempts = n_failures + spare_attempts
    counter = {"calls": 0}
    sleeper = MagicMock()

    @retry(
        max_attempts=max_attempts,
        base_delay=0.01,
        sleeper=sleeper,
        rng=random.Random(0),
    )
    def func() -> int:
        counter["calls"] += 1
        if counter["calls"] <= n_failures:
            raise TransientError("transient")
        return 42

    assert func() == 42
    assert counter["calls"] == n_failures + 1
    assert sleeper.call_count == n_failures


@given(max_attempts=st.integers(min_value=1, max_value=6))
@settings(max_examples=20, deadline=None)
def test_retry_raises_after_exhausting_attempts(max_attempts: int) -> None:
    """When every attempt fails transiently, the last exception bubbles."""
    sleeper = MagicMock()
    counter = {"calls": 0}

    @retry(
        max_attempts=max_attempts,
        base_delay=0.01,
        sleeper=sleeper,
        rng=random.Random(0),
    )
    def func() -> None:
        counter["calls"] += 1
        raise TransientError("always")

    with pytest.raises(TransientError):
        func()
    assert counter["calls"] == max_attempts
    # No final sleep after the last attempt fails.
    assert sleeper.call_count == max_attempts - 1


@given(
    max_attempts=st.integers(min_value=2, max_value=8),
    base_delay=st.floats(min_value=0.001, max_value=1.0),
    max_delay=st.floats(min_value=1.0, max_value=10.0),
    seed=st.integers(min_value=0, max_value=10_000),
)
@settings(
    max_examples=30,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
def test_retry_sleep_intervals_respect_max_delay(
    max_attempts: int, base_delay: float, max_delay: float, seed: int
) -> None:
    """Every sleep interval falls within [0, max_delay], regardless of attempt."""
    sleeper = MagicMock()

    @retry(
        max_attempts=max_attempts,
        base_delay=base_delay,
        max_delay=max_delay,
        sleeper=sleeper,
        rng=random.Random(seed),
    )
    def func() -> None:
        raise TransientError("always")

    with pytest.raises(TransientError):
        func()

    intervals = [call.args[0] for call in sleeper.call_args_list]
    assert all(0.0 <= w <= max_delay for w in intervals)


# =============================================================================
# validate_contract — roundtrip and rejection
# =============================================================================


class _Sample(BaseModel):
    id: int
    name: str
    value: float


@given(
    id_=st.integers(min_value=-(2**31), max_value=2**31 - 1),
    name=st.text(min_size=1, max_size=100),
    value=st.floats(allow_nan=False, allow_infinity=False),
)
def test_validate_contract_returns_instance_for_satisfying_dict(
    id_: int, name: str, value: float
) -> None:
    """Any dict that satisfies the schema produces a model instance."""
    result = validate_contract({"id": id_, "name": name, "value": value}, _Sample)
    assert result.id == id_
    assert result.name == name
    assert result.value == value


@given(
    extras=st.dictionaries(
        st.text(min_size=1, max_size=20),
        st.text(max_size=50),
        max_size=5,
    ).filter(lambda d: not (set(d) & {"id", "name", "value"})),
)
def test_validate_contract_ignores_extra_keys(extras: dict[str, str]) -> None:
    """Pydantic v2 default config drops unknown fields silently.

    Asserts against ``model_dump()`` and ``model_fields_set`` rather than
    ``hasattr`` because BaseModel inherits ``__dict__``, ``__class__``,
    ``model_*`` methods etc. that match arbitrary attribute names.
    """
    payload: dict[str, object] = {"id": 1, "name": "x", "value": 1.0, **extras}
    result = validate_contract(payload, _Sample)
    assert result.id == 1
    dumped = result.model_dump()
    for extra_key in extras:
        assert extra_key not in dumped
        assert extra_key not in result.model_fields_set


@given(missing=st.sampled_from(["id", "name", "value"]))
def test_validate_contract_raises_when_required_field_missing(missing: str) -> None:
    """Removing any required field always raises ContractValidationError."""
    payload = {"id": 1, "name": "x", "value": 1.0}
    payload.pop(missing)
    with pytest.raises(ContractValidationError):
        validate_contract(payload, _Sample)


# =============================================================================
# traceparent — roundtrip
# =============================================================================


@given(trace_id=_TRACE_ID, span_id=_SPAN_ID, sampled=st.booleans())
def test_build_then_parse_traceparent_roundtrips(
    trace_id: str, span_id: str, sampled: bool
) -> None:
    """``parse(build(t, s))`` always returns ``(t, s)`` for valid hex."""
    header = build_traceparent(trace_id, span_id, sampled=sampled)
    assert parse_traceparent(header) == (trace_id, span_id)


@given(
    junk=st.text(
        alphabet=st.characters(blacklist_categories=("Cc", "Cs")), max_size=200
    )
)
def test_parse_traceparent_never_raises(junk: str) -> None:
    """Even on adversarial input, parse_traceparent must return None or a tuple."""
    result = parse_traceparent(junk)
    assert result is None or (isinstance(result, tuple) and len(result) == 2)
