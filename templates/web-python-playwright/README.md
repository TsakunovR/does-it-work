# WEB-автотесты: Playwright + pytest + Allure

Каркас UI-тестов. **Проверенный запуском пример на реальном SPA RV Booker**
(6 тестов, зелёные) — замените Page Object'ы на страницы своего приложения,
сохранив структуру и паттерны.

## Установка и запуск

```bash
uv venv .venv --python 3.12
uv pip install --python .venv/bin/python -r requirements.txt
.venv/bin/playwright install chromium

PYTHONPATH=. .venv/bin/pytest                      # весь сьют (дефолт pytest-playwright — chromium)
PYTHONPATH=. .venv/bin/pytest --browser firefox    # другой браузер (в addopts --browser не задан:
                                                   # флаг накопительный, иначе гонялись бы оба)
PYTHONPATH=. .venv/bin/pytest -m smoke             # быстрый смоук
```

Окружение — через `WEB_TESTS_*` (см. `config.py` и `.env.example`);
`WEB_TESTS_SECRET_CODE` обязателен — без него подготовка пользователя через API
падает с понятной ошибкой.

## Ключевые паттерны

- **Page Object**: страница = класс, локаторы = свойства-`Locator`, действия = методы
  с `allure.step`. Тесты не трогают селекторы напрямую.
- **Логин через API** (`authorized_page`): токен кладётся в localStorage в обход формы —
  быстро и стабильно; сама форма логина проверяется отдельными UI-тестами.
- **Подготовка данных — только через API** (`api/auth.py`), UI-тесты не создают
  состояние кликами.
- **Артефакты при падении**: скриншот + HTML в Allure (hook в conftest),
  плюс `--screenshot=only-on-failure --tracing=retain-on-failure` в pytest.ini.
- **Никакого networkidle**: SPA держит фоновые запросы — готовность страницы
  проверяют `expect(locator).to_be_visible()`.
- **Мобильные вьюпорты**: фикстура `mobile_page` (390×844) для адаптивной вёрстки.
- **Селекторы**: стабильные id (`#login-email-input`) → роли (`get_by_role`) → css;
  хрупкие xpath по индексам запрещены.

## Gotchas (найдены при реальном прогоне)

- **`networkidle` на SPA может не наступать никогда** (фоновые поллинги/websocket) —
  `page.goto(..., wait_until="networkidle")` зависает до таймаута. Ждите
  `domcontentloaded` + `expect(locator).to_be_visible()` конкретных элементов.
- **Разведайте DOM до написания Page Object'ов**: откройте живое приложение
  playwright-скриптом, снимите реальные id/роли. Придуманные селекторы — главная
  причина красных UI-тестов.
- **Логин через API**: выясните разведкой, где фронт хранит сессию (localStorage-ключ,
  cookie) и что именно кладёт (у RV Booker — `booking_user` = JSON с token и user);
  инжектируйте до перехода в авторизованную зону.
