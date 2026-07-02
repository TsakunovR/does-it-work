"""Фикстуры UI-тестов: пользователь через API, авторизованная страница, артефакты."""
import json
import platform
import shutil
from pathlib import Path

import allure
import pytest

from api.auth import delete_account, register_user
from config import settings

# Все фикстуры, отдающие Page: хук артефактов перебирает их при падении теста
PAGE_FIXTURES = ("page", "authorized_page", "mobile_page")


def pytest_configure(config):
    """environment.properties и категории дефектов — как в API-каркасе:
    Allure подхватывает categories.json только из папки с результатами."""
    results_dir = config.getoption("--alluredir")
    if results_dir:
        results = Path(results_dir)
        results.mkdir(parents=True, exist_ok=True)
        (results / "environment.properties").write_text(
            f"BASE_URL={settings.base_url}\nPYTHON={platform.python_version()}\nMODE=web-e2e\n",
            encoding="utf-8",
        )
        categories = Path(__file__).parent.parent / "allure-categories.json"
        if categories.exists():
            shutil.copy(categories, results / "categories.json")


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Артефакты при падении: скриншот и HTML страницы уходят в Allure."""
    outcome = yield
    report = outcome.get_result()
    if report.when == "call" and report.failed:
        for name in PAGE_FIXTURES:
            page = item.funcargs.get(name)
            if page is None or page.is_closed():
                continue
            # try/except обязателен: если страница умерла вместе с тестом,
            # упавший хук даёт INTERNALERROR pytest и маскирует причину падения
            try:
                allure.attach(
                    page.screenshot(full_page=True),
                    name=f"Скриншот при падении ({name})",
                    attachment_type=allure.attachment_type.PNG,
                )
                allure.attach(
                    page.content(),
                    name=f"HTML страницы ({name})",
                    attachment_type=allure.attachment_type.HTML,
                )
            except Exception as exc:
                allure.attach(
                    f"Не удалось снять артефакты со страницы «{name}»: {exc}",
                    name=f"Артефакты недоступны ({name})",
                    attachment_type=allure.attachment_type.TEXT,
                )


@pytest.fixture
def api_user():
    """Свежий пользователь, созданный через API; аккаунт удаляется в teardown."""
    user = register_user()
    yield user
    delete_account(user["token"])


@pytest.fixture
def authorized_page(context, api_user):
    """Страница с авторизацией через API в обход формы логина:
    токен кладётся в localStorage (фронт хранит сессию в ключе booking_user).
    Сама форма логина проверяется отдельными UI-тестами."""
    page = context.new_page()
    page.goto(settings.base_url, wait_until="domcontentloaded")
    page.evaluate(
        "value => localStorage.setItem('booking_user', value)",
        json.dumps({"token": api_user["token"], "user": api_user["user"]}),
    )
    yield page
    page.close()


@pytest.fixture
def mobile_page(new_context):
    """Страница с мобильным вьюпортом (iPhone-подобный размер).
    Контекст создаём через фабрику pytest-playwright (`new_context`), а не
    `browser.new_context`: только так на мобильный тест действуют
    `--tracing=retain-on-failure` и `--screenshot=only-on-failure` из pytest.ini
    (плагин регистрирует артефакты и закрывает контекст в teardown сам).
    Глобальный `browser_context_args` для этого не годится — он задал бы мобильный
    вьюпорт всем тестам и сломал бы десктопные проверки лендинга.
    Для проверки адаптивности достаточно viewport; is_mobile не используем —
    Firefox его не поддерживает, и тест падал бы в кросс-браузерной матрице."""
    context = new_context(viewport={"width": 390, "height": 844})
    return context.new_page()
