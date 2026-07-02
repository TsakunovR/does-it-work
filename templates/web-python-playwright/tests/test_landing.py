"""Лендинг: доступность и адаптивность."""
import allure
import pytest
from playwright.sync_api import expect

from pages.landing_page import LandingPage

pytestmark = pytest.mark.e2e


@allure.feature("Лендинг")
class TestLanding:
    @allure.title("Главная страница открывается: заголовок и кнопка входа видны")
    @allure.severity(allure.severity_level.BLOCKER)
    @pytest.mark.smoke
    def test_landing_opens(self, page):
        landing = LandingPage(page).open()

        expect(landing.title_heading).to_be_visible()
        expect(landing.login_button).to_be_visible()

    @allure.title("Мобильный вьюпорт: показывается бургер-меню вместо десктопной навигации")
    @allure.severity(allure.severity_level.NORMAL)
    def test_landing_mobile_viewport(self, mobile_page):
        landing = LandingPage(mobile_page).open()

        expect(landing.title_heading).to_be_visible()
        expect(landing.mobile_menu_toggle).to_be_visible()
        expect(landing.login_button).not_to_be_visible()
