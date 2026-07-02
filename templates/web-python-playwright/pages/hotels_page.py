"""Каталог отелей (авторизованная зона)."""
import allure
from playwright.sync_api import Locator

from pages.base_page import BasePage


class HotelsPage(BasePage):
    path = "/hotels"

    @property
    def heading(self) -> Locator:
        return self.page.get_by_role("heading", name="Найдите идеальный отель")

    @property
    def search_input(self) -> Locator:
        return self.page.locator("#hotel-search-input")

    @property
    def hotel_cards(self) -> Locator:
        # Контейнер карточки — div с id вида hotel-card-<id>; вложенные элементы
        # с тем же префиксом (name, кнопки) — другие теги, div-фильтра достаточно
        return self.page.locator("div[id^=hotel-card-]")

    @property
    def hotel_names(self) -> Locator:
        return self.page.locator("[id^=hotel-card-name-]")

    def search(self, query: str) -> None:
        with allure.step(f"Ищем отель: «{query}»"):
            self.search_input.fill(query)
