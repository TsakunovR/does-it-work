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
    timeout: float = 15.0  # секунды

    @property
    def timeout_ms(self) -> int:
        """Таймаут в миллисекундах — для ожиданий Playwright."""
        return int(self.timeout * 1000)


settings = Settings()
