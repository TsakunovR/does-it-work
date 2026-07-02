# API-автотесты на Java (JUnit 5 + REST Assured + Allure)

Каркас e2e-тестов HTTP API. **Это проверенный запуском пример на реальном API
RV Booker** (12 тестов, зелёные) — замените клиентов/модели/тесты на свои ресурсы,
сохранив структуру слоёв.

## Требования

JDK 21+, Maven 3.9+.

## Запуск

```bash
mvn test                                   # весь сьют (flaky исключён: excludedGroups в pom)
mvn test -Dgroups=smoke                    # быстрый смоук
mvn test -Dgroups=critical                 # бизнес-критичные потоки
mvn test -Dgroups=flaky -DexcludedGroups=  # карантин отдельно (пустой -DexcludedGroups= снимает исключение)
```

Карантин работает потому, что `excludedGroups` задан **maven-свойством** в `pom.xml`,
а surefire ссылается на него как `${excludedGroups}` — CLI-флаг `-DexcludedGroups=`
переопределяет свойство. Хардкод внутри `<configuration>` CLI бы не перекрыл.

### Переменные окружения

Только env `API_TESTS_*` (см. `TestConfig`), как и в python-каркасе; `.env`-файлов нет —
java-стек читает окружение напрямую:

| Переменная                 | Дефолт                              | Назначение                                        |
|----------------------------|-------------------------------------|---------------------------------------------------|
| `API_TESTS_BASE_URL`       | `https://rvtravel.rv-school.ru/api` | Базовый URL API                                   |
| `API_TESTS_SECRET_CODE`    | `TESTCODE2025`                      | Секретный код регистрации                         |
| `API_TESTS_ADMIN_EMAIL`    | — (пусто)                           | Email админа; пусто — админские тесты скипаются   |
| `API_TESTS_ADMIN_PASSWORD` | — (пусто)                           | Пароль админа                                     |
| `API_TESTS_TIMEOUT_MS`     | `10000`                             | Connection/socket таймаут HTTP-запросов, мс       |

```bash
API_TESTS_BASE_URL=https://staging.example.com/api mvn test
```

## Отчёт Allure

Результаты в `target/allure-results` (задано в `allure.properties`);
`environment.properties` и `categories.json` (копия `allure-categories.json`
из корня проекта) пишет `AllureEnvironmentListener` — платформенный
`TestExecutionListener` (регистрируется через ServiceLoader), поэтому окружение
появляется на старте ЛЮБОГО прогона, в т.ч. одиночного `mvn test -Dtest=HealthTests`:

```bash
allure serve target/allure-results
```

## Структура

```
src/test/java/booker/
  config/TestConfig.java        # env-конфигурация (API_TESTS_*)
  clients/BaseClient.java       # given().spec(...): baseUri, JSON, Allure-фильтр, токен
  clients/<Resource>Client.java # клиент на ресурс; тесты не строят запросы сами
  models/*.java                 # records = строгие контракты (Jackson падает на лишних полях)
  utils/ApiAssertions.java      # assertStatus / assertContract / assertError + Allure.step
  utils/TestDataFactory.java    # уникальные данные, никаких хардкодов
  support/AllureEnvironmentListener.java  # environment.properties + categories.json на старте прогона
  tests/BaseTest.java           # сессионный пользователь на класс (register/@BeforeAll → delete/@AfterAll)
  tests/*Tests.java             # тесты по фичам; @Tag: e2e/smoke/critical/negative/flaky
  tests/KnownBugsTests.java     # подтверждённые баги API: assert корректного поведения + @Tag flaky (карантин)
allure-categories.json          # категории падений для Allure-отчёта
```

## Ключевые паттерны

- **Контракты через records**: Jackson с дефолтными настройками падает на неизвестных
  полях — аналог pydantic `extra="forbid"`. Имена компонентов = имена JSON-полей.
- **Асинхронные операции — Awaitility** (`await().atMost(...).untilAsserted(...)`),
  `Thread.sleep` запрещён.
- **Ретрай конфликтов общего стенда** — цикл с новыми случайными данными
  (см. `createBooking` в `BookingLifecycleTests`).
- Теги = маркеры python-каркаса; severity — `@Severity(SeverityLevel...)`.

## Gotchas (найдены при реальном прогоне)

- **Спека из `RequestSpecBuilder.build()` — «незапущенная»**: вызов `.post()/.get()`
  прямо на ней падает с `NullPointer: Cannot get property 'assertionClosure' on null
  object`. Оборачивайте: `RestAssured.given().spec(builder.build())`.
- **Вызовы клиентов в `@BeforeAll`/`@AfterAll` шумят** `ERROR AllureLifecycle: no test
  is running` — безвредно (вне тестового контекста Allure некуда крепить шаги);
  глушится системным свойством `org.slf4j.simpleLogger.log.io.qameta.allure=off`
  в surefire (см. pom).
- **Jackson по умолчанию строгий** — падает на неизвестных полях: records без
  аннотаций уже дают контракт уровня pydantic `extra="forbid"`. Не отключайте
  `FAIL_ON_UNKNOWN_PROPERTIES` глобально.
