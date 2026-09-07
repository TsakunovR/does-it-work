# Ветка api-python: структура, паттерны, запуск, gotchas

Детали ветки, вынесенные из SKILL.md, чтобы точка входа осталась про маршрутизацию.
Читать при генерации api-python — и как образец при генерации остальных веток:
слои, таксономия маркеров, порядок запуска у них те же, отличается синтаксис.
Специфика остальных веток — в README соответствующего шаблона.

Эталон всего описанного здесь — `templates/api-python/`: копируйте структуру
и стиль оттуда, а не пишите с нуля.

## Структура каркаса

```
api-tests/
  config.py               # pydantic-settings: base_url, токены — из env (API_TESTS_*)
  clients/
    base.py               # BaseApiClient: allure.step + вложения «Запрос»/«Ответ»
    <resource>.py          # клиент на ресурс: create/get/list/delete + create_raw
  models/
    <resource>.py          # Pydantic-модели ответов, extra="forbid"
  utils/
    assertions.py          # assert_status / assert_contract / assert_error (allure.step внутри)
    waiters.py             # wait_until: поллинг асинхронных операций вместо time.sleep
    retry.py               # retry-декоратор с экспоненциальным backoff (сетевые сбои)
    soft.py                # SoftAssertions: все расхождения одним отчётом
  tests/
    __init__.py            # обязателен здесь и в каждой поддиректории (см. Gotchas)
    conftest.py            # http_client (2 режима), фабрики faker, created_* с teardown
    <feature>/             # директория = фича; файл = сценарная группа, ≤1 класса на файл
      __init__.py
      test_lifecycle.py    # happy path + полный жизненный цикл
      test_validation.py   # параметризованные негативные (400/404/422)
      test_access.py       # авторизация и доступ (401/403)
  pytest.ini               # testpaths, --alluredir, маркеры (см. таксономию ниже)
  requirements.txt
  .env.example             # шаблон всех API_TESTS_*-переменных с комментариями
  README.md                # установка, запуск, переключение окружений, CI-матрица
  allure-categories.json   # категории дефектов Allure (копирует pytest_configure из conftest)
  .github/workflows/api-tests.yml  # CI: e2e по пушу/кнопке/расписанию, артефакт allure-results
```

## Обязательные паттерны

Все реализованы в `templates/api-python/`:

- **Тесты не вызывают HTTP напрямую** — только через методы клиентов. Клиент возвращает
  `httpx.Response`, проверки статуса и тела — в тесте.
- **Проверки — через `utils/assertions.py`**, не голыми assert: `assert_status(resp, 201)`,
  `model = assert_contract(resp, UserResponse)`, `assert_error(resp, 404, context=case_id)` —
  каждый даёт Allure-шаг и читаемое сообщение; доменные проверки полей остаются
  обычными assert рядом.
- **Асинхронные операции — только `wait_until` из `utils/waiters.py`**, `time.sleep`
  в тестах запрещён. Если API отвечает «принято в обработку» (202/processing) —
  это отдельный тест: дождись конечного статуса поллингом и проверь его.
- **Таксономия маркеров** (registered в pytest.ini): `smoke` — минимальный быстрый
  набор ключевых сценариев, `critical` — бизнес-критичные потоки, `negative` —
  негативные, `flaky` — карантин (CI гоняет `-m "not flaky"`). Плюс `@allure.severity`
  на каждом тесте: blocker — ключевые happy path, critical — авторизация/доступ,
  normal — остальное, minor — 404 и косметика.
  В web- и java-ветках дополнительно маркер/тег `e2e` на всех тестах (они всегда
  идут против живого стенда); в api-python его нет — режим e2e/asgi задаёт
  env-переменная `API_TESTS_MODE`, а не маркер.
- **`create_raw(payload: dict)`** в каждом клиенте — для негативных кейсов с произвольным телом.
- **Контракт через Pydantic**: `UserResponse.model_validate(response.json())` с
  `extra="forbid"` — ловит лишние поля, типы и обязательность. Тела ошибок тоже
  валидируются моделью (`ApiError`).
- **Негативные кейсы** — один параметризованный тест, кейсы вида `("случай", payload)`,
  человекочитаемый `case_id` идёт в сообщение assert.
- **Тестовые данные** — фабрики на `faker` (фикстура `user_payload`), никаких хардкодов.
- **Очистка** — фикстура `created_*` создаёт ресурс и удаляет в teardown; teardown не
  падает, если тест уже удалил ресурс сам.
- **Каждый негативный позитивному в пару**: на любой happy path — минимум кейсы
  «невалидное тело» (422), «без авторизации» (401), «не существует» (404).
- **Группировка по фиче, не по типу теста** (выбор пользователя): директория = фича,
  файл = сценарная группа, не больше одного класса на файл (класс в pytest — только
  пространство имён и `allure.story`). Негативные кейсы лежат рядом со своей фичей,
  а не в общем «негативном» файле; запуск фичи целиком — `pytest tests/<feature>`.
  Allure-иерархия: feature = директория, story = файл/класс.
- **README.md обязателен во всех ветках** (шаблоны в `templates/`): механизм
  переключения окружений должен быть виден без чтения config.py — примеры запуска
  в терминале и CI-матрица сред. **`.env.example` обязателен в python-ветках**
  (pydantic-settings читает `.env`); в java-ветках dotenv-механизма нет — Java-стек
  читает env-переменные напрямую, поэтому вместо `.env.example` в README должна быть
  полная таблица env-переменных с описанием и дефолтами.
- **Живой стенд и динамическая авторизация** — если токен не статический
  (register/login, роли admin/user, общий стенд с чужими данными), бери проверенные
  паттерны из [live-api-patterns.md](live-api-patterns.md):
  `session_user`/`temp_user`, skip позитивного админского CRUD без кредов,
  ретрай при конфликте ресурсов, уникальные суффиксы в данных.
  Для ветки api-java — Java-эквиваленты там же (`@BeforeAll`-пользователь,
  `@BeforeEach`-temp-пользователь, `Assumptions.assumeTrue`, Awaitility).


## Запуск: режимы и артефакты

Сгенерированные, но не запущенные тесты — не результат. Установка и smoke-проверка
окружения — готовыми скриптами из директории скилла (запускать из корня
сгенерированного проекта, путь к скрипту — полный, до директории скилла):
python-ветки — `scripts/bootstrap.sh` (venv + зависимости + проверка коллекции
тестов), java-ветки — `scripts/bootstrap-java.sh` (проверка java/mvn +
`mvn test-compile`).

Что делает `scripts/bootstrap.sh` (эквивалент вручную, проверено):

```bash
uv venv .venv --python 3.12
uv pip install --python .venv/bin/python -r requirements.txt
PYTHONPATH=. .venv/bin/pytest --collect-only -q    # проверка коллекции тестов
```

Стенда нет вообще (демо, обучение, проверка каркаса)? Поднимите заглушку из
директории скилла — она реализует ровно тот контракт, на который написан
`templates/api-python`:

```bash
cd <директория-скилла>/fixtures/stub-api && uv run --with 'fastapi[standard]' uvicorn main:app --port 8000
```

Интеграционный режим (in-process, без развёрнутого стенда — если приложение импортируемо):

```bash
API_TESTS_MODE=asgi PYTHONPATH=.:<путь-к-приложению> .venv/bin/pytest
```

E2E против стенда:

```bash
API_TESTS_BASE_URL=https://staging.example.com API_TESTS_API_TOKEN=... PYTHONPATH=. .venv/bin/pytest
```

Allure-результаты пишутся в `allure-results/` (задано в pytest.ini); отчёт:
`allure serve allure-results`. Категории дефектов (`allure-categories.json` в корне
проекта) подкладывает в results хук `pytest_configure` из conftest — известные баги
(strict xfail с текстом «Баг API: …») попадают в отдельную категорию отчёта.
Тренды/история Allure появляются, только если переносить `history/` из прошлого
отчёта в новые results — в CI сохраняйте отчёт артефактом или публикуйте на Pages.

Если тест падает из-за реального расхождения API со спекой —
не подгоняй тест под фактическое поведение молча: покажи расхождение пользователю.
Подтверждённый баг фиксируй тестом с `xfail(reason="Баг API: ...", strict=True)` —
прогон остаётся зелёным, а когда баг починят, тест сам просигналит (XPASS→FAILED).

Найденные баги API в итоговом отчёте пользователю классифицируй по severity
(шаблон — [../examples/bug-report.md](../examples/bug-report.md)):
**Critical** — потеря денег/данных, дыры авторизации; **High** — функция не работает
или спека врёт о ключевом поведении; **Medium** — принимаются невалидные данные,
неверные коды ошибок; **Low** — расхождения форматов, косметика.

## Моки и параллельность

- Моки внешних API (когда тестируем свой сервис in-process, а он ходит наружу) — `respx`:
  `respx.mock` фикстурой, роуты на конкретные URL, `assert_all_called`.
- Параллельность — `pytest-xdist` (`-n auto`); тесты обязаны быть независимыми
  (свои данные через фабрики, очистка в teardown) — паттерны шаблона это гарантируют.

## Gotchas (найдены при реальном прогоне)

- **`EmailStr` требует `email-validator`**: ставьте `pydantic[email]`, иначе падение
  на этапе сборки схемы модели (`ImportError` при коллекции тестов).
- **`httpx.ASGITransport` — только async.** С синхронным `httpx.Client` он падает с
  `AttributeError: 'ASGITransport' object has no attribute 'handle_request'`.
  Для sync in-process тестов используйте `fastapi.testclient.TestClient` — он наследник
  `httpx.Client`, поэтому API-клиенты каркаса работают с ним без изменений.
- **Кириллические id в `parametrize`** в выводе терминала экранируются
  (`\u043f\u0443...` вместо `пу...`) — это косметика pytest, в Allure-отчёте всё читаемо. Если мешает,
  добавьте `disable_test_id_escaping_and_forfeit_all_rights_to_community_support = True`
  в pytest.ini.
- **`TestClient(app, headers=...)`** принимает заголовки в конструкторе — токен
  авторизации задаётся один раз, как и у сетевого клиента.
- **Пустая env-переменная не «сбрасывает» настройку**: `API_TESTS_BASE_URL= pytest`
  задаёт пустую строку (перекрывая и `.env`, и дефолт) — тесты падают с
  `httpx.UnsupportedProtocol`. Проверяйте, не экспортирована ли переменная пустой.
- **Одинаковые имена тест-файлов в разных директориях** (`users/test_validation.py`
  и `bookings/test_validation.py`) без `__init__.py` роняют коллекцию pytest
  с «import file mismatch». Кладите пустой `__init__.py` в `tests/` и каждую
  поддиректорию — заодно это делает надёжными импорты вида `from tests.factories import`.

Выше — gotchas ветки api-python. Gotchas остальных веток (api-java, все web) —
в разделе «Gotchas» README соответствующего шаблона: прочитай его перед
генерацией своей ветки.
