"""Каталог отелей: авторизованная зона (вход через API в обход формы)."""
import re

import allure
import pytest
from playwright.sync_api import expect

from config import settings
from pages.hotels_page import HotelsPage

pytestmark = [pytest.mark.e2e, pytest.mark.critical]


@allure.feature("Каталог отелей")
class TestHotels:
    @allure.title("Каталог отелей показывает карточки (вход через API)")
    @allure.severity(allure.severity_level.BLOCKER)
    @pytest.mark.smoke
    def test_hotels_list_visible(self, authorized_page):
        hotels = HotelsPage(authorized_page).open()

        expect(hotels.heading).to_be_visible()
        expect(hotels.hotel_names.first).to_be_visible(timeout=settings.timeout_ms)
        # not_to_have_count(0) сам поллит — не полагаемся на то, что карточки уже
        # отрисованы к моменту снятия count (голый .count() без ожидания хрупок)
        expect(hotels.hotel_cards).not_to_have_count(0, timeout=settings.timeout_ms)

    @allure.title("Поиск фильтрует карточки по названию отеля")
    @allure.severity(allure.severity_level.NORMAL)
    def test_hotels_search_filters(self, authorized_page):
        hotels = HotelsPage(authorized_page).open()
        expect(hotels.hotel_names.first).to_be_visible(timeout=settings.timeout_ms)
        first_name = hotels.hotel_names.first.text_content()
        assert first_name and first_name.strip(), "не удалось прочитать название первого отеля"
        first_name = first_name.strip()
        pattern = re.compile(re.escape(first_name), re.IGNORECASE)

        hotels.search(first_name)

        with allure.step(f"В выдаче остаются только отели с «{first_name}»"):
            # Ожидание привязано к результату фильтрации: expect сам поллит,
            # пока карточки без искомого текста не исчезнут из выдачи
            expect(hotels.hotel_names.filter(has_not_text=pattern)).to_have_count(
                0, timeout=settings.timeout_ms
            )
            # ...и фильтр не спрятал всё: первая карточка содержит запрос
            expect(hotels.hotel_names.first).to_contain_text(
                pattern, timeout=settings.timeout_ms
            )
