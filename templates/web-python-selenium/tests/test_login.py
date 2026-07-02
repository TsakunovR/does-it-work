"""Логин через UI-форму: happy path и негативный сценарий."""
import allure
import pytest
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from config import settings
from pages.login_page import LoginPage

pytestmark = [pytest.mark.e2e, pytest.mark.critical]


@allure.feature("Авторизация")
@allure.story("Форма логина")
class TestLogin:
    @allure.title("Успешный логин ведёт в каталог отелей и сохраняет сессию")
    @allure.severity(allure.severity_level.BLOCKER)
    @pytest.mark.smoke
    def test_login_success(self, driver, api_user):
        login = LoginPage(driver).open()

        login.login(api_user["email"], api_user["password"])

        with allure.step("Редирект в каталог отелей"):
            WebDriverWait(driver, settings.timeout).until(EC.url_contains("/hotels"))
        with allure.step("Сессия сохранена в localStorage"):
            stored = driver.execute_script("return localStorage.getItem('booking_user')")
            assert stored is not None, "после логина нет booking_user в localStorage"

    @allure.title("Логин с неверным паролем не пускает в систему")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.negative
    def test_login_wrong_password(self, driver, api_user):
        login = LoginPage(driver).open()

        login.login(api_user["email"], "wrong-password-123")

        with allure.step("Показана ошибка, остаёмся на /login, сессия не создана"):
            # Сначала ждём видимого признака завершения запроса — сообщения об ошибке;
            # мгновенные ассерты сразу после click() пропускали бы поздний редирект
            assert login.visible(login.ERROR_MESSAGE).is_displayed()
            assert "/login" in driver.current_url, f"неожиданный редирект: {driver.current_url}"
            stored = driver.execute_script("return localStorage.getItem('booking_user')")
            assert stored is None, "сессия не должна создаваться при неверном пароле"
