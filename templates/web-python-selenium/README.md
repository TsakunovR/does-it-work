# WEB-автотесты: Selenium + pytest + Allure

Каркас UI-тестов на классическом Selenium. **Проверенный запуском пример на реальном
SPA RV Booker** (4 теста, зелёные). Если выбираете стек с нуля и легаси не требует
Selenium — рассмотрите Playwright-вариант (`web-python-playwright`): меньше бойлерплейта.

## Установка и запуск

```bash
uv venv .venv --python 3.12
uv pip install --python .venv/bin/python -r requirements.txt

PYTHONPATH=. .venv/bin/pytest              # Chrome headless
PYTHONPATH=. .venv/bin/pytest -m smoke
```

Окружение — через `WEB_TESTS_*` (см. `config.py` и `.env.example`);
`WEB_TESTS_SECRET_CODE` обязателен — без него подготовка пользователя через API
падает с понятной ошибкой.

## Ключевые паттерны

- **Page Object**: локаторы — кортежи `(By.ID, ...)` константами класса, действия —
  методы с `allure.step`.
- **Явные ожидания обязательны**: доступ к элементам только через
  `BasePage.visible(locator)` (WebDriverWait + expected_conditions);
  голый `find_element` и `time.sleep` запрещены.
- **Логин через API** (`authorized_driver`): токен кладётся в localStorage в обход
  формы — быстро и стабильно; сама форма логина проверяется отдельными UI-тестами.
- **Подготовка данных — только через API** (`api/auth.py`).
- **Артефакты при падении**: скриншот + page_source в Allure (hook в conftest).
- **Селекторы**: стабильные id → роли/атрибуты → css; хрупкие xpath запрещены.

## Gotchas (найдены при реальном прогоне)

- **Разведайте DOM до написания Page Object'ов**: откройте живое приложение
  playwright- или selenium-скриптом, снимите реальные id/роли. Придуманные
  селекторы — главная причина красных UI-тестов.
- **Логин через API**: выясните разведкой, где фронт хранит сессию (localStorage-ключ,
  cookie) и что именно кладёт (у RV Booker — `booking_user` = JSON с token и user);
  инжектируйте до перехода в авторизованную зону.
- **Selenium + свежий Chrome**: предупреждения `Unable to find CDP implementation`
  косметические (CDP-маппинг отстаёт от браузера), тесты работают.
