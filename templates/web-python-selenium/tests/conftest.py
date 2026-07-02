"""Фикстуры Selenium-тестов: драйвер, пользователь через API, артефакты при падении."""
import json
import platform
import shutil
from pathlib import Path

import allure
import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from api.auth import delete_account, register_user
from config import settings


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
        driver = item.funcargs.get("driver") or item.funcargs.get("authorized_driver")
        if driver:
            # try/except обязателен: если сессия браузера умерла вместе с тестом,
            # упавший хук даёт INTERNALERROR pytest и маскирует причину падения
            try:
                allure.attach(
                    driver.get_screenshot_as_png(),
                    name="Скриншот при падении",
                    attachment_type=allure.attachment_type.PNG,
                )
                allure.attach(
                    driver.page_source,
                    name="HTML страницы",
                    attachment_type=allure.attachment_type.HTML,
                )
            except Exception as exc:
                allure.attach(
                    f"Не удалось снять артефакты с драйвера: {exc}",
                    name="Артефакты недоступны",
                    attachment_type=allure.attachment_type.TEXT,
                )


@pytest.fixture
def driver():
    """Chrome headless; драйвер подбирает Selenium Manager автоматически."""
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1440,900")
    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(settings.timeout)
    yield driver
    driver.quit()


@pytest.fixture
def api_user():
    """Свежий пользователь, созданный через API; аккаунт удаляется в teardown."""
    user = register_user()
    yield user
    delete_account(user["token"])


@pytest.fixture
def authorized_driver(driver, api_user):
    """Драйвер с авторизацией через API в обход формы логина:
    токен кладётся в localStorage (фронт хранит сессию в ключе booking_user).
    Сама форма логина проверяется отдельными UI-тестами."""
    driver.get(settings.base_url)
    driver.execute_script(
        "localStorage.setItem('booking_user', arguments[0])",
        json.dumps({"token": api_user["token"], "user": api_user["user"]}),
    )
    return driver
