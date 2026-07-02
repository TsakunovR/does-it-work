"""Повтор операций при временных сбоях (сеть, 5xx) с экспоненциальным backoff."""
import functools
import time
from typing import Callable, TypeVar

import httpx

T = TypeVar("T")


def retry(
    times: int = 3,
    backoff: float = 0.5,
    exceptions: tuple[type[Exception], ...] = (httpx.TransportError,),
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Декоратор: до times попыток, пауза backoff × 2^n между ними.
    Повторяет только перечисленные исключения — ошибки логики пробрасываются сразу."""

    def decorator(fn: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(fn)
        def wrapper(*args, **kwargs) -> T:
            for attempt in range(times):
                try:
                    return fn(*args, **kwargs)
                except exceptions:
                    if attempt == times - 1:
                        raise
                    time.sleep(backoff * 2**attempt)
            raise AssertionError("unreachable")

        return wrapper

    return decorator
