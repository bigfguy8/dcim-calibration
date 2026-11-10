"""
Exponential-backoff retry helper for flaky I/O operations.

Used for git push, file copies over slow storage, and any transient failure
that deserves a graceful recovery instead of an immediate abort.
"""

from __future__ import annotations

import random
import time
from typing import Callable, Iterable, Type, TypeVar

T = TypeVar("T")


class RetryExhaustedError(RuntimeError):
    """Raised when all retry attempts have been exhausted."""


def call_with_retry(
    func: Callable[..., T],
    *args,
    max_retries: int = 3,
    backoff: float = 1.0,
    exceptions: tuple[type[BaseException], ...] = (Exception,),
    on_retry: Callable[[int, BaseException], None] | None = None,
    **kwargs,
) -> T:
    """
    Call *func* with retries and exponential backoff (+ jitter).

    Parameters
    ----------
    func:
        Callable to invoke.
    max_retries:
        Number of *retry* attempts after the first failure.
    backoff:
        Base delay in seconds; delay = backoff * 2**attempt + jitter.
    exceptions:
        Exception types that trigger a retry. All other exceptions propagate.
    on_retry:
        Optional callback(attempt, exception) invoked before each retry.
    """
    last_exc: BaseException | None = None
    attempts = max_retries + 1
    for attempt in range(attempts):
        try:
            return func(*args, **kwargs)
        except exceptions as exc:
            last_exc = exc
            if attempt == attempts - 1:
                break
            if on_retry is not None:
                try:
                    on_retry(attempt + 1, exc)
                except Exception:
                    pass
            # Exponential backoff with jitter so concurrent daemons don't
            # thundering-herd on the same transient failure.
            delay = backoff * (2 ** attempt) + random.uniform(0, backoff)
            time.sleep(delay)
    assert last_exc is not None
    raise RetryExhaustedError(
        f"Operation failed after {attempts} attempts: {last_exc}"
    ) from last_exc


def retry(
    *,
    max_retries: int = 3,
    backoff: float = 1.0,
    exceptions: tuple[type[BaseException], ...] = (Exception,),
    on_retry: Callable[[int, BaseException], None] | None = None,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator form of :func:`call_with_retry`."""

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        def wrapper(*args, **kwargs) -> T:
            return call_with_retry(
                func,
                *args,
                max_retries=max_retries,
                backoff=backoff,
                exceptions=exceptions,
                on_retry=on_retry,
                **kwargs,
            )

        return wrapper

    return decorator
