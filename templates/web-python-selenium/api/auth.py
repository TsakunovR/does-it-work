"""Подготовка данных через API: UI-тесты не должны готовить состояние через UI."""
import random

import httpx

from config import settings


def register_user() -> dict:
    """Регистрирует свежего пользователя, возвращает email/password/token/user."""
    if not settings.secret_code:
        raise RuntimeError(
            "Секретный код регистрации не задан: задайте WEB_TESTS_SECRET_CODE "
            "в .env или переменных окружения (см. .env.example)"
        )
    email = f"qa.web.{random.randint(100_000, 999_999)}.{random.randint(100_000, 999_999)}@example.com"
    password = f"Qa{random.randint(10_000_000, 99_999_999)}!"
    response = httpx.post(
        f"{settings.api_url}/auth/register",
        json={"email": email, "password": password, "secret_code": settings.secret_code},
        timeout=settings.timeout,
    )
    # не assert: с python -O проверка исчезла бы, а это подготовка данных, не тестовая проверка
    if response.status_code != 201:
        raise RuntimeError(
            f"Не удалось зарегистрировать пользователя: {response.status_code} {response.text}"
        )
    body = response.json()
    return {"email": email, "password": password, "token": body["token"], "user": body["user"]}


def delete_account(token: str) -> None:
    """Удаляет аккаунт; не падает, если он уже удалён."""
    httpx.delete(
        f"{settings.api_url}/users/me",
        headers={"Authorization": f"Bearer {token}"},
        timeout=settings.timeout,
    )
