"""Пользователи: happy path каждого действия и полный жизненный цикл."""
import allure
import pytest

from models.users import UserResponse
from utils.assertions import assert_contract, assert_error, assert_status
from utils.soft import SoftAssertions

pytestmark = pytest.mark.critical


@allure.feature("Пользователи")
@allure.story("Жизненный цикл")
class TestUsersLifecycle:
    @allure.title("Создание пользователя: 201 и корректный контракт ответа")
    @allure.severity(allure.severity_level.BLOCKER)
    @pytest.mark.smoke
    def test_create_user(self, users_api, user_payload):
        response = users_api.create(**user_payload)

        assert_status(response, 201)
        body = response.json()
        # Без id нечем делать teardown — падаем с понятным сообщением, а не голым
        # KeyError где-то ниже. Дальше id уже есть, поэтому очистку в finally
        # заводим только с этой точки.
        assert "id" in body, "в ответе создания нет id"
        user_id = body["id"]
        # Очистка в finally: иначе при падении ассертов ниже пользователь утёк бы
        # на стенд. delete не проверяет статус, поэтому teardown не упадёт,
        # даже если ресурс уже удалён.
        try:
            user = assert_contract(response, UserResponse)
            with SoftAssertions() as soft:
                soft.check(user.name == user_payload["name"], "имя не совпадает с запросом")
                soft.check(user.email == user_payload["email"], "email не совпадает с запросом")
                soft.check(user.age == user_payload["age"], "возраст не совпадает с запросом")
        finally:
            users_api.delete(user_id)

    @allure.title("Получение созданного пользователя по id")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_user(self, users_api, created_user):
        response = users_api.get(created_user["id"])

        assert_status(response, 200)
        user = assert_contract(response, UserResponse)
        assert user.id == created_user["id"]

    @allure.title("Созданный пользователь появляется в списке")
    @allure.severity(allure.severity_level.NORMAL)
    def test_user_in_list(self, users_api, created_user):
        response = users_api.list()

        assert_status(response, 200)
        users = [UserResponse.model_validate(item) for item in response.json()]
        assert created_user["id"] in [u.id for u in users]

    @allure.title("Полный цикл: создание → чтение → удаление → 404")
    @allure.severity(allure.severity_level.BLOCKER)
    def test_full_lifecycle(self, users_api, user_payload):
        with allure.step("Создаём пользователя"):
            created = users_api.create(**user_payload)
            assert_status(created, 201)
            user_id = created.json()["id"]

        with allure.step("Пользователь доступен по id"):
            assert_status(users_api.get(user_id), 200)

        with allure.step("Удаляем пользователя"):
            assert_status(users_api.delete(user_id), 204)

        with allure.step("После удаления возвращается 404"):
            assert_error(users_api.get(user_id), 404)
