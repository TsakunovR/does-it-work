# API-автотесты <сервис>

E2E и интеграционные тесты HTTP API: pytest + httpx + Pydantic-контракты + Allure.
Покрытие: happy path, полный жизненный цикл ресурсов и негативные кейсы
(валидация, авторизация, несуществующие ресурсы).

## Установка

```bash
uv venv .venv --python 3.12
uv pip install --python .venv/bin/python -r requirements.txt
```

## Запуск

E2E против стенда (по умолчанию — адрес из `config.py`):

```bash
PYTHONPATH=. .venv/bin/pytest                  # весь сьют
PYTHONPATH=. .venv/bin/pytest -m smoke         # быстрый смоук
PYTHONPATH=. .venv/bin/pytest -m critical      # бизнес-критичные потоки
PYTHONPATH=. .venv/bin/pytest -m "not flaky"   # без карантина (режим CI)
PYTHONPATH=. .venv/bin/pytest tests/<feature>  # одна фича
```

Интеграционный режим in-process (без развёрнутого стенда, если приложение импортируемо):

```bash
API_TESTS_MODE=asgi PYTHONPATH=.:<путь-к-приложению> .venv/bin/pytest
```

### Запуск на другом окружении

Вся конфигурация — через переменные окружения с префиксом `API_TESTS_`
(см. `config.py`, значения по умолчанию — в `.env.example`):

| Переменная            | Назначение                                            | Дефолт                  |
| --------------------- | ----------------------------------------------------- | ----------------------- |
| `API_TESTS_BASE_URL`  | Базовый URL стенда (без завершающего `/`)              | `http://127.0.0.1:8000` |
| `API_TESTS_API_TOKEN` | Токен авторизации                                      | `secret-token`          |
| `API_TESTS_TIMEOUT`   | Таймаут HTTP-запросов, секунды                         | `10`                    |
| `API_TESTS_MODE`      | `e2e` — по сети против стенда, `asgi` — in-process     | `e2e`                   |

```bash
# разовый запуск на другом стенде
API_TESTS_BASE_URL=https://staging.example.com API_TESTS_API_TOKEN=... PYTHONPATH=. .venv/bin/pytest

# постоянная настройка для локальной работы — через .env-файл
cp .env.example .env   # и поправьте значения; .env в git не коммитится
PYTHONPATH=. .venv/bin/pytest
```

Приоритет источников: **переменная окружения → `.env` → дефолт в `config.py`**.

### CI на нескольких средах

Среда задаётся переменными джобы, код и команда запуска не меняются.
Пример для GitHub Actions:

```yaml
jobs:
  e2e:
    strategy:
      matrix:
        include:
          - env_name: staging
            base_url: https://staging.example.com
          - env_name: prod
            base_url: https://api.example.com
    steps:
      - run: PYTHONPATH=. pytest -m "not flaky"
        env:
          API_TESTS_BASE_URL: ${{ matrix.base_url }}
          API_TESTS_API_TOKEN: ${{ secrets.API_TESTS_API_TOKEN }}
```

Секреты передавайте только через переменные окружения — флаги командной строки
попадают в логи CI. Готовый workflow лежит в `.github/workflows/api-tests.yml`:
запуск по пушу, по кнопке (с выбором стенда) и по расписанию, `allure-results`
сохраняются артефактом.

## Отчёт Allure

Результаты пишутся в `allure-results/` (настроено в `pytest.ini`):

```bash
allure serve allure-results
```

Категории дефектов (`allure-categories.json`) подкладываются в результаты
автоматически (`pytest_configure` в conftest): известные баги API (strict xfail),
расхождения контракта и сетевые ошибки видны в отчёте отдельными группами.

## Структура

Группировка тестов: **директория = фича, файл = сценарная группа** (не больше одного
класса на файл, негативные кейсы лежат рядом со своей фичей). Запуск одной фичи:
`pytest tests/<feature>`.

```
config.py                    # pydantic-settings: все настройки из env (API_TESTS_*)
clients/                     # API-клиенты по ресурсам; тесты не ходят в HTTP напрямую
models/                      # Pydantic-контракты ответов, extra="forbid"
utils/                       # assertions (шаги + сообщения), waiters, retry, soft
allure-categories.json       # категории дефектов для Allure-отчёта
.github/workflows/           # CI: e2e-прогон + Allure на GitHub Pages с трендами
tests/
  __init__.py                # обязателен здесь и в каждой поддиректории
  conftest.py                # фикстуры: HTTP-клиент (2 режима), фабрики faker, авто-очистка
  <feature>/
    __init__.py
    test_lifecycle.py        # happy path + полный жизненный цикл
    test_validation.py       # параметризованные негативные (400/404/422)
    test_access.py           # авторизация и доступ (401/403)
```
