"""Конфигурация тестового окружения через переменные окружения / .env."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="WEB_TESTS_", env_file=".env", extra="ignore")

    base_url: str = "https://rvtravel.rv-school.ru"
    # API того же стенда — для подготовки данных и логина в обход UI
    api_url: str = "https://rvtravel.rv-school.ru/api"
    # Секретный код регистрации — без дефолта в коде: задайте WEB_TESTS_SECRET_CODE
    # в .env или переменных окружения (см. .env.example)
    secret_code: str = ""
    timeout: float = 15.0  # секунды — и для httpx, и для WebDriverWait


settings = Settings()
