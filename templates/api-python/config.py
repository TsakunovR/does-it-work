"""Конфигурация тестового окружения через переменные окружения / .env."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # extra="ignore" оставлен сознательно: .env может быть общим с приложением
    # и содержать переменные без префикса API_TESTS_ — они не должны валить тесты.
    model_config = SettingsConfigDict(env_prefix="API_TESTS_", env_file=".env", extra="ignore")

    base_url: str = "http://127.0.0.1:8000"
    api_token: str = "secret-token"
    timeout: float = 10.0
    mode: str = "e2e"  # e2e — по сети против стенда | asgi — in-process через TestClient


settings = Settings()
