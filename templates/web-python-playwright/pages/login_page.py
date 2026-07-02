"""Страница логина."""
import allure
from playwright.sync_api import Locator

from pages.base_page import BasePage


class LoginPage(BasePage):
    path = "/login"

    @property
    def email_input(self) -> Locator:
        return self.page.locator("#login-email-input")

    @property
    def password_input(self) -> Locator:
        return self.page.locator("#login-password-input")

    @property
    def submit_button(self) -> Locator:
        return self.page.locator("button[type=submit]")

    @property
    def error_message(self) -> Locator:
        return self.page.locator("#login-error")

    def login(self, email: str, password: str) -> None:
        with allure.step(f"Логинимся через форму: {email}"):
            self.email_input.fill(email)
            self.password_input.fill(password)
            self.submit_button.click()
