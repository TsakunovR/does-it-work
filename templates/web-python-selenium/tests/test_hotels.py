"""Каталог отелей: авторизованная зона (вход через API в обход формы)."""
import allure
import pytest

from pages.hotels_page import HotelsPage

pytestmark = [pytest.mark.e2e, pytest.mark.critical]


@allure.feature("Каталог отелей")
class TestHotels:
    @allure.title("Каталог отелей показывает карточки (вход через API)")
    @allure.severity(allure.severity_level.BLOCKER)
    @pytest.mark.smoke
    def test_hotels_list_visible(self, authorized_driver):
        hotels = HotelsPage(authorized_driver).open()

        first_name = hotels.visible(hotels.HOTEL_NAMES)
        assert first_name.text.strip(), "у первой карточки отеля пустое название"
        assert hotels.cards_count() > 0, "в каталоге нет ни одной карточки отеля"
