"""Страница логина."""
import allure
from selenium.webdriver.common.by import By

from pages.base_page import BasePage


class LoginPage(BasePage):
    path = "/login"

    EMAIL_INPUT = (By.ID, "login-email-input")
    PASSWORD_INPUT = (By.ID, "login-password-input")
    SUBMIT_BUTTON = (By.CSS_SELECTOR, "button[type=submit]")
    ERROR_MESSAGE = (By.ID, "login-error")

    def login(self, email: str, password: str) -> None:
        with allure.step(f"Логинимся через форму: {email}"):
            self.visible(self.EMAIL_INPUT).send_keys(email)
            self.visible(self.PASSWORD_INPUT).send_keys(password)
            self.visible(self.SUBMIT_BUTTON).click()
