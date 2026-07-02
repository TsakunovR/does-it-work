"""Базовый API-клиент: логирование запросов/ответов в Allure, единая точка HTTP."""
import json

import allure
import httpx


class BaseApiClient:
    """Обёртка над httpx.Client. Тесты не делают HTTP-вызовы напрямую —
    только через методы клиентов-наследников."""

    def __init__(self, http: httpx.Client):
        self._http = http

    def _request(self, method: str, url: str, **kwargs) -> httpx.Response:
        with allure.step(f"{method} {url}"):
            response = self._http.request(method, url, **kwargs)
            self._attach(response)
            return response

    @staticmethod
    def _attach(response: httpx.Response) -> None:
        request = response.request
        allure.attach(
            f"{request.method} {request.url}\n\n{request.content.decode('utf-8', 'replace')}",
            name="Запрос",
            attachment_type=allure.attachment_type.TEXT,
        )
        try:
            body = json.dumps(response.json(), ensure_ascii=False, indent=2)
        except (json.JSONDecodeError, ValueError):
            body = response.text
        allure.attach(
            f"HTTP {response.status_code}\n\n{body}",
            name="Ответ",
            attachment_type=allure.attachment_type.TEXT,
        )
