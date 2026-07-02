"""Базовый Page Object: навигация и общие элементы шапки."""
import allure
from playwright.sync_api import Page

from config import settings


class BasePage:
    path = "/"

    def __init__(self, page: Page):
        self.page = page

    def open(self) -> "BasePage":
        """Не ждём networkidle: SPA держит фоновые запросы, и оно не наступает.
        Готовность страницы проверяют локаторы конкретных элементов."""
        with allure.step(f"Открываем {self.path}"):
            self.page.goto(settings.base_url + self.path, wait_until="domcontentloaded")
        return self
