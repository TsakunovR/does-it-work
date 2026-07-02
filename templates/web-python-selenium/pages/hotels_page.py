"""Каталог отелей (авторизованная зона)."""
import allure
from selenium.webdriver.common.by import By

from pages.base_page import BasePage


class HotelsPage(BasePage):
    path = "/hotels"

    # Контейнер карточки — div с id вида hotel-card-<id>; вложенные элементы
    # с тем же префиксом (name, кнопки) — другие теги, div-фильтра достаточно
    HOTEL_CARDS = (By.CSS_SELECTOR, "div[id^=hotel-card-]")
    HOTEL_NAMES = (By.CSS_SELECTOR, "[id^=hotel-card-name-]")

    def cards_count(self) -> int:
        """Число карточек в каталоге. Доступ к элементам — только через
        страницу; ожидание видимости первой карточки делает тест до вызова."""
        with allure.step("Считаем карточки отелей"):
            return len(self.driver.find_elements(*self.HOTEL_CARDS))
