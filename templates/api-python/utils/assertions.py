"""Переиспользуемые проверки: Allure-шаг + читаемое сообщение об ошибке.

Убирают копипасту `assert response.status_code == ..., response.text`
и делают шаги проверок видимыми в отчёте.
"""
import allure
import httpx
from pydantic import BaseModel

from models.common import ApiError


def assert_status(response: httpx.Response, expected: int, context: str = "") -> None:
    """Проверяет HTTP-статус; в сообщении — контекст кейса и тело ответа."""
    prefix = f"Кейс «{context}»: " if context else ""
    with allure.step(f"Статус ответа = {expected}"):
        assert response.status_code == expected, (
            f"{prefix}ожидали {expected}, получили {response.status_code}: {response.text}"
        )


def assert_contract(response: httpx.Response, model: type[BaseModel]) -> BaseModel:
    """Валидирует тело ответа Pydantic-моделью и возвращает её экземпляр."""
    with allure.step(f"Контракт ответа: {model.__name__}"):
        return model.model_validate(response.json())


def assert_error(response: httpx.Response, expected_status: int, context: str = "") -> ApiError:
    """Негативный кейс одним вызовом: статус + контракт тела ошибки."""
    assert_status(response, expected_status, context)
    return assert_contract(response, ApiError)
