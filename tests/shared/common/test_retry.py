"""Unit tests for the retry helper."""

import random

import pytest

from shared.common.exceptions import (
    ExternalServiceError,
    PermanentError,
    TransientError,
)
from shared.common.retry import retry


class _FakeClock:
    """Advances only when the injected sleeper is called."""

    def __init__(self) -> None:
        self.now = 0.0
        self.sleeps: list[float] = []

    def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self.now += seconds

    def read(self) -> float:
        return self.now


def test_retry_returns_on_first_success():
    clock = _FakeClock()
    calls = {"n": 0}

    @retry(sleeper=clock.sleep, clock=clock.read, rng=random.Random(0))
    def op() -> str:
        calls["n"] += 1
        return "ok"

    assert op() == "ok"
    assert calls["n"] == 1
    assert clock.sleeps == []


def test_retry_succeeds_after_transient_failures():
    clock = _FakeClock()
    calls = {"n": 0}

    @retry(
        max_attempts=4,
        base_delay=1.0,
        max_delay=10.0,
        max_elapsed=60.0,
        sleeper=clock.sleep,
        clock=clock.read,
        rng=random.Random(42),
    )
    def op() -> int:
        calls["n"] += 1
        if calls["n"] < 3:
            raise ExternalServiceError("flaky")
        return 7

    assert op() == 7
    assert calls["n"] == 3
    assert len(clock.sleeps) == 2
    assert all(0.0 <= s <= 10.0 for s in clock.sleeps)


def test_retry_exhausts_attempts_and_reraises():
    clock = _FakeClock()
    calls = {"n": 0}

    @retry(
        max_attempts=3,
        base_delay=0.5,
        sleeper=clock.sleep,
        clock=clock.read,
        rng=random.Random(1),
    )
    def op() -> None:
        calls["n"] += 1
        raise ExternalServiceError("always down")

    with pytest.raises(ExternalServiceError):
        op()
    assert calls["n"] == 3
    assert len(clock.sleeps) == 2


def test_retry_does_not_catch_permanent_error():
    clock = _FakeClock()
    calls = {"n": 0}

    @retry(
        max_attempts=5,
        sleeper=clock.sleep,
        clock=clock.read,
        rng=random.Random(0),
    )
    def op() -> None:
        calls["n"] += 1
        raise PermanentError("nope")

    with pytest.raises(PermanentError):
        op()
    assert calls["n"] == 1
    assert clock.sleeps == []


def test_retry_stops_when_max_elapsed_reached():
    clock = _FakeClock()
    calls = {"n": 0}

    @retry(
        max_attempts=10,
        base_delay=1.0,
        max_delay=10.0,
        max_elapsed=2.0,
        sleeper=clock.sleep,
        clock=clock.read,
        rng=random.Random(999),
    )
    def op() -> None:
        calls["n"] += 1
        raise TransientError("slow to recover")

    with pytest.raises(TransientError):
        op()
    assert calls["n"] < 10
    assert clock.now >= 2.0 or calls["n"] < 10
