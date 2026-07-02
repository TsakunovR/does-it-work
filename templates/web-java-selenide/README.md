# WEB-автотесты: Selenide + JUnit 5 + Allure

Каркас UI-тестов. **Проверенный запуском пример на реальном SPA RV Booker**
(изначально 3 теста, зелёные). Замените Page Object'ы на страницы своего приложения.

## Требования

JDK 21+, Maven 3.9+, Chrome.

## Запуск

```bash
mvn test                                   # весь сьют, headless Chrome (flaky исключён: excludedGroups в pom)
mvn test -Dgroups=smoke                    # быстрый смоук
mvn test -Dgroups=flaky -DexcludedGroups=  # карантин отдельно (пустой -DexcludedGroups= снимает исключение)
```

Карантин работает потому, что `excludedGroups` задан **maven-свойством** в `pom.xml`,
а surefire ссылается на него как `${excludedGroups}` — CLI-флаг `-DexcludedGroups=`
переопределяет свойство. Хардкод внутри `<configuration>` CLI бы не перекрыл.

### Переменные окружения

Только env `WEB_TESTS_*` (см. `WebConfig`); `.env`-файлов нет — java-стек читает
окружение напрямую:

| Переменная              | Дефолт                              | Назначение                                  |
|-------------------------|-------------------------------------|---------------------------------------------|
| `WEB_TESTS_BASE_URL`    | `https://rvtravel.rv-school.ru`     | Базовый URL приложения                       |
| `WEB_TESTS_API_URL`     | `https://rvtravel.rv-school.ru/api` | API того же стенда (подготовка данных)       |
| `WEB_TESTS_SECRET_CODE` | `TESTCODE2025`                      | Секретный код регистрации                    |
| `WEB_TESTS_HEADLESS`    | `true`                              | `false` — смотреть прогон в живом браузере   |
| `WEB_TESTS_TIMEOUT_MS`  | `10000`                             | Connection/socket таймаут HTTP-подготовки данных, мс |

```bash
WEB_TESTS_BASE_URL=https://staging.example.com WEB_TESTS_HEADLESS=false mvn test
```

## CI (GitHub Actions)

`.github/workflows/web-tests-java.yml` — прогон на `push` в `main` и вручную
(`workflow_dispatch`, можно передать `base_url`). Одна джоба на `ubuntu-latest`
по образцу api-java: `setup-java` (JDK 21 + кэш Maven) → `mvn -B test` →
артефакт `target/allure-results` при `always()`.

Особенности UI-прогона:

- **Chrome** предустановлен в `ubuntu-latest`; Selenide/Selenium Manager сам
  подтягивает совместимый драйвер. Отдельная установка не нужна — только шаг
  проверки версии.
- **`WEB_TESTS_HEADLESS=true`** экспортируется всегда: дисплея в раннере нет.
- Стенд задаётся через `vars.WEB_TESTS_BASE_URL` / `vars.WEB_TESTS_API_URL` /
  `secrets.WEB_TESTS_SECRET_CODE`. **Экспортируются только непустые** значения —
  пустой env перекрыл бы дефолт из `WebConfig`.
- Карантин flaky исключается дефолтным `excludedGroups=flaky` из `pom.xml`.

## Отчёт Allure

Результаты в `target/allure-results` (задано в `allure.properties`);
`environment.properties` и `categories.json` (копия `allure-categories.json`
из корня проекта) пишет `BaseUiTest`:

```bash
allure serve target/allure-results
```

## Структура

```
src/test/java/web/
  config/WebConfig.java     # env-конфигурация (WEB_TESTS_*)
  api/ApiAuth.java          # подготовка данных через API (stdlib HttpClient, без зависимостей)
  pages/*.java              # Page Object: SelenideElement-поля + @Step-методы
  tests/BaseUiTest.java     # Configuration + AllureSelenide + loginViaApi (логин в обход UI)
  tests/*Tests.java         # тесты; @Tag: e2e/smoke/critical/negative/flaky
allure-categories.json      # категории падений для Allure-отчёта
```

## Ключевые паттерны

- **AllureSelenide-листенер** даёт шаги, скриншоты и page source при падении из коробки.
- **Ожидания встроены**: `$(...).shouldBe(visible)` сам ждёт; `Thread.sleep` запрещён.
- **Подготовка данных — только через API** (`ApiAuth`), UI-тесты не создают состояние кликами.
- **Логин через API в обход UI** — `loginViaApi(user)` в `BaseUiTest`: открывает базовую
  страницу и кладёт сессию в `localStorage` (ключ `booking_user`), тесты авторизованной
  зоны не тратят время на форму логина (см. `HotelsTests`). Сама форма проверяется
  отдельными UI-тестами (`LoginTests`).
- Селекторы: стабильные id (`#login-email-input`) → css; хрупкие xpath запрещены.
- Предупреждения `Unable to find CDP implementation` в логах — косметика
  (версия Chrome новее селениумовского CDP-маппинга), на тесты не влияют.

## Gotchas (найдены при реальном прогоне)

- **Разведайте DOM до написания Page Object'ов**: откройте живое приложение
  (playwright-скриптом или Selenide в headed-режиме), снимите реальные id/роли.
  Придуманные селекторы — главная причина красных UI-тестов.
- **Логин через API**: выясните разведкой, где фронт хранит сессию (localStorage-ключ,
  cookie) и что именно кладёт (у RV Booker — `booking_user` = JSON с token и user);
  инжектируйте до перехода в авторизованную зону (см. `loginViaApi` в `BaseUiTest`).
