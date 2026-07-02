"""Клиент эндпоинтов /users — аналог Page Object для API."""
import httpx

from clients.base import BaseApiClient


class UsersClient(BaseApiClient):
    def create(self, name: str, email: str, age: int) -> httpx.Response:
        return self._request("POST", "/users", json={"name": name, "email": email, "age": age})

    def create_raw(self, payload: dict) -> httpx.Response:
        """Для негативных кейсов: произвольное тело без валидации на клиенте."""
        return self._request("POST", "/users", json=payload)

    def get(self, user_id: str) -> httpx.Response:
        return self._request("GET", f"/users/{user_id}")

    def list(self) -> httpx.Response:
        return self._request("GET", "/users")

    def delete(self, user_id: str) -> httpx.Response:
        return self._request("DELETE", f"/users/{user_id}")
