"""Retry helper with exponential backoff and full jitter.

Implements the single retry policy described in
``docs/guides/error-handling.md`` §4. Only :class:`TransientError` (and
subclasses) is retried by default; permanent failures propagate immediately.

The decorator injects ``sleeper``, ``clock``, and ``rng`` so tests can drive
deterministic behaviour without patching builtins.
"""

from collections.abc import Callable
from functools import wraps
import logging
import random
import time
from typing import ParamSpec, TypeVar

from .exceptions import TransientError

P = ParamSpec("P")
R = TypeVar("R")


def retry(
    *,
    max_attempts: int = 3,
    base_delay: float = 0.2,
    max_delay: float = 10.0,
    max_elapsed: float = 30.0,
    retry_on: tuple[type[BaseException], ...] = (TransientError,),
    sleeper: Callable[[float], None] = time.sleep,
    clock: Callable[[], float] = time.monotonic,
    rng: random.Random | None = None,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Retry ``retry_on`` failures with exponential backoff + full jitter.

    Args:
        max_attempts: Maximum number of attempts (including the first).
        base_delay: Initial backoff delay in seconds; doubled each attempt.
        max_delay: Upper bound on a single wait interval.
        max_elapsed: Upper bound on total wall-clock time across attempts.
        retry_on: Exception classes that trigger another attempt.
        sleeper: Callable used to wait between attempts. Injected for tests.
        clock: Monotonic clock reading seconds. Injected for tests.
        rng: Random source for full-jitter sampling. Injected for tests.

    Returns:
        A decorator that wraps a callable with retry behaviour.
    """
    _rng = rng if rng is not None else random.Random()

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        func_name = getattr(func, "__qualname__", repr(func))

        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            start = clock()
            last_exc: BaseException | None = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except retry_on as err:
                    last_exc = err
                    elapsed = clock() - start
                    if attempt >= max_attempts or elapsed >= max_elapsed:
                        logging.error(
                            "retry giving up",
                            extra={
                                "extra_fields": {
                                    "reason_code": getattr(
                                        err, "reason_code", "transient"
                                    ),
                                    "function": func_name,
                                    "attempt": attempt,
                                    "max_attempts": max_attempts,
                                    "elapsed_s": elapsed,
                                }
                            },
                        )
                        raise
                    exp = min(max_delay, base_delay * (2 ** (attempt - 1)))
                    wait = _rng.uniform(0.0, exp)
                    logging.warning(
                        "retrying after transient failure",
                        extra={
                            "extra_fields": {
                                "reason_code": getattr(err, "reason_code", "transient"),
                                "function": func_name,
                                "attempt": attempt,
                                "wait_s": wait,
                            }
                        },
                    )
                    sleeper(wait)
            assert last_exc is not None  # pragma: no cover - loop guarantees this
            raise last_exc

        return wrapper

    return decorator
