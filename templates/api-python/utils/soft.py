"""Мягкие проверки: копим все несоответствия и падаем одним отчётом.

Для длинных контрактных проверок, где важно увидеть сразу все расхождения,
а не чинить их по одному за прогон.
"""
import allure


class SoftAssertions:
    """Контекст-менеджер: soft.check(условие, "сообщение") внутри,
    единый AssertionError со списком всех провалов на выходе."""

    def __init__(self) -> None:
        self._failures: list[str] = []

    def check(self, condition: bool, message: str) -> None:
        # assert внутри шага: провалившаяся проверка видна в отчёте красным
        # (шаг завершается исключением). Само исключение перехватываем и копим —
        # тест продолжается, единый AssertionError поднимется в __exit__.
        try:
            with allure.step(f"Проверка: {message}"):
                assert condition, message
        except AssertionError:
            self._failures.append(message)

    def __enter__(self) -> "SoftAssertions":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if exc_type is None and self._failures:
            details = "\n  - ".join(self._failures)
            raise AssertionError(f"мягкие проверки провалены ({len(self._failures)}):\n  - {details}")
