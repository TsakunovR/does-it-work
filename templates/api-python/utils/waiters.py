"""Ожидание асинхронных операций поллингом — вместо слепого time.sleep."""
import time
from typing import Callable, TypeVar

import allure

T = TypeVar("T")


def wait_until(
    probe: Callable[[], T],
    until: Callable[[T], bool],
    *,
    timeout: float = 20.0,
    interval: float = 1.0,
    description: str = "условие выполнится",
) -> T:
    """Опрашивает probe() каждые interval секунд, пока until(результат) не станет
    истинным. Возвращает последний результат; по таймауту падает с ним же в сообщении."""
    with allure.step(f"Ждём, пока {description} (таймаут {timeout:g}с)"):
        deadline = time.monotonic() + timeout
        last: T = probe()
        while not until(last):
            if time.monotonic() >= deadline:
                raise AssertionError(
                    f"не дождались, пока {description}, за {timeout:g}с; "
                    f"последнее состояние: {last!r}"
                )
            time.sleep(interval)
            last = probe()
        return last
