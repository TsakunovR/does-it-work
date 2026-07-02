"""Логин через UI-форму: happy path и негативный сценарий."""
import allure
import pytest
from playwright.sync_api import expect

from config import settings
from pages.login_page import LoginPage

pytestmark = [pytest.mark.e2e, pytest.mark.critical]


@allure.feature("Авторизация")
@allure.story("Форма логина")
class TestLogin:
    @allure.title("Успешный логин ведёт в каталог отелей и сохраняет сессию")
    @allure.severity(allure.severity_level.BLOCKER)
    @pytest.mark.smoke
    def test_login_success(self, page, api_user):
        login = LoginPage(page).open()

        login.login(api_user["email"], api_user["password"])

        with allure.step("Редирект в каталог отелей"):
            page.wait_for_url("**/hotels", timeout=settings.timeout_ms)
        with allure.step("Сессия сохранена в localStorage"):
            stored = page.evaluate("() => localStorage.getItem('booking_user')")
            assert stored is not None, "после логина нет booking_user в localStorage"

    @allure.title("Логин с неверным паролем не пускает в систему")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.negative
    def test_login_wrong_password(self, page, api_user):
        login = LoginPage(page).open()

        # Ждём ответ сервера на сам запрос логина: без этого ассерты ниже
        # выполнялись бы до завершения запроса и пропускали поздний редирект
        with page.expect_response("**/auth/login") as response_info:
            login.login(api_user["email"], "wrong-password-123")

        with allure.step("Сервер отклонил логин"):
            assert not response_info.value.ok, (
                f"ожидали отказ сервера, получили {response_info.value.status}"
            )
        with allure.step("Показана ошибка, остаёмся на /login, сессия не создана"):
            expect(login.error_message).to_be_visible()
            expect(login.email_input).to_be_visible()
            assert "/login" in page.url, f"неожиданный редирект: {page.url}"
            stored = page.evaluate("() => localStorage.getItem('booking_user')")
            assert stored is None, "сессия не должна создаваться при неверном пароле"
