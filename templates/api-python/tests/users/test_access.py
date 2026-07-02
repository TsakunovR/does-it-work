"""Пользователи: авторизация и доступ."""
import allure
import pytest

from clients.users import UsersClient
from utils.assertions import assert_error

pytestmark = pytest.mark.negative


@allure.feature("Пользователи")
@allure.story("Авторизация")
class TestUsersAccess:
    @allure.title("Запрос без токена возвращает 401 с телом ошибки")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_no_token(self, anonymous_client):
        response = UsersClient(anonymous_client).list()
        assert_error(response, 401, context="без токена")
