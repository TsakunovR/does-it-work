"""Лендинг (главная страница до авторизации)."""
from playwright.sync_api import Locator

from pages.base_page import BasePage


class LandingPage(BasePage):
    path = "/"

    @property
    def title_heading(self) -> Locator:
        return self.page.get_by_role("heading", name="Бронируйте отели просто и надёжно")

    @property
    def login_button(self) -> Locator:
        return self.page.locator("#public-login-btn")

    @property
    def mobile_menu_toggle(self) -> Locator:
        return self.page.locator("#public-mobile-menu-toggle")
