"""Пользователи: валидация тела запроса и несуществующие ресурсы."""
import allure
import pytest

from utils.assertions import assert_error

pytestmark = pytest.mark.negative


@allure.feature("Пользователи")
@allure.story("Валидация входных данных")
class TestUsersValidation:
    @allure.title("Невалидное тело запроса отклоняется: {case_id}")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.parametrize(
        ("case_id", "payload"),
        [
            ("пустое имя", {"name": "", "email": "a@b.ru", "age": 30}),
            ("нет email", {"name": "Иван", "age": 30}),
            ("email не email", {"name": "Иван", "email": "не-почта", "age": 30}),
            ("отрицательный возраст", {"name": "Иван", "email": "a@b.ru", "age": -1}),
            ("возраст больше 150", {"name": "Иван", "email": "a@b.ru", "age": 151}),
            ("возраст строкой", {"name": "Иван", "email": "a@b.ru", "age": "тридцать"}),
            ("пустое тело", {}),
        ],
    )
    def test_create_invalid(self, users_api, case_id, payload):
        response = users_api.create_raw(payload)

        assert_error(response, 422, context=case_id)

    @allure.title("Несуществующий пользователь: 404 с телом ошибки")
    @allure.severity(allure.severity_level.MINOR)
    def test_get_missing_user(self, users_api):
        assert_error(users_api.get("00000000-0000-0000-0000-000000000000"), 404)
