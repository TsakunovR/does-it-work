"""Фикстуры: HTTP-клиент, API-клиенты, фабрика данных, авто-очистка."""
import platform
import shutil
from pathlib import Path

import httpx
import pytest
from faker import Faker

from clients.users import UsersClient
from config import settings

fake = Faker("ru_RU")


def pytest_sessionfinish(session, exitstatus):
    """environment.properties для Allure: в отчёте видно, против какого стенда гоняли."""
    results_dir = session.config.getoption("--alluredir")
    if results_dir:
        Path(results_dir).mkdir(parents=True, exist_ok=True)
        (Path(results_dir) / "environment.properties").write_text(
            f"BASE_URL={settings.base_url}\nPYTHON={platform.python_version()}\nMODE={settings.mode}\n",
            encoding="utf-8",
        )


def pytest_configure(config):
    """Кладёт категории дефектов в allure-results: сам Allure файл из корня
    проекта не подхватывает — categories.json должен лежать рядом с результатами."""
    results_dir = config.getoption("--alluredir")
    categories = Path(__file__).parent.parent / "allure-categories.json"
    if results_dir and categories.exists():
        Path(results_dir).mkdir(parents=True, exist_ok=True)
        shutil.copy(categories, Path(results_dir) / "categories.json")


@pytest.fixture(scope="session")
def http_client() -> httpx.Client:
    """Сессионный httpx.Client.

    API_TESTS_MODE=asgi — гоняет запросы в приложение in-process, без сети
    (интеграционный режим); иначе ходит по base_url (e2e против стенда).

    Важно: httpx.ASGITransport асинхронный и с sync-клиентом не работает.
    Для sync in-process тестов используем TestClient — он наследник
    httpx.Client, поэтому API-клиенты каркаса работают с ним без изменений.
    """
    headers = {"Authorization": f"Bearer {settings.api_token}"}
    if settings.mode == "asgi":
        from fastapi.testclient import TestClient

        from your_app.main import app  # TODO: замените на импорт тестируемого приложения

        client = TestClient(app, headers=headers)
    else:
        client = httpx.Client(
            base_url=settings.base_url, headers=headers, timeout=settings.timeout
        )
    yield client
    client.close()


@pytest.fixture(scope="session")
def anonymous_client() -> httpx.Client:
    """Клиент без токена — для тестов авторизации."""
    if settings.mode == "asgi":
        from fastapi.testclient import TestClient

        from your_app.main import app  # TODO: замените на импорт тестируемого приложения

        client = TestClient(app)
    else:
        client = httpx.Client(base_url=settings.base_url, timeout=settings.timeout)
    yield client
    client.close()


@pytest.fixture
def users_api(http_client) -> UsersClient:
    return UsersClient(http_client)


@pytest.fixture
def user_payload() -> dict:
    """Фабрика валидных данных пользователя."""
    return {"name": fake.name(), "email": fake.email(), "age": fake.random_int(18, 90)}


@pytest.fixture
def created_user(users_api, user_payload) -> dict:
    """Создаёт пользователя перед тестом и удаляет после (teardown не падает,
    если тест уже удалил его сам)."""
    response = users_api.create(**user_payload)
    assert response.status_code == 201, response.text
    user = response.json()
    yield user
    users_api.delete(user["id"])
