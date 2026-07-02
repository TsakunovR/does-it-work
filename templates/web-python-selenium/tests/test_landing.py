"""Лендинг: доступность ключевых элементов."""
import allure
import pytest

from pages.landing_page import LandingPage

pytestmark = pytest.mark.e2e


@allure.feature("Лендинг")
class TestLanding:
    @allure.title("Главная страница открывается: заголовок и кнопка входа видны")
    @allure.severity(allure.severity_level.BLOCKER)
    @pytest.mark.smoke
    def test_landing_opens(self, driver):
        landing = LandingPage(driver).open()

        heading = landing.visible(landing.TITLE_HEADING)
        assert "Бронируйте отели" in heading.text, f"неожиданный заголовок: {heading.text!r}"
        assert landing.visible(landing.LOGIN_BUTTON).is_displayed()
