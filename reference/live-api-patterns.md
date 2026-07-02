# Паттерны для живого API: динамическая авторизация и общий стенд

Код ниже взят из реального проекта (RV Booker, 60 тестов, зелёные) — копируйте
структуру, подставляя свои эндпоинты. Примеры — на Python (ветка api-python);
Java-эквиваленты тех же паттернов — в конце документа.

## Динамическая авторизация (когда статического токена нет)

Шаблонный `config.py` предполагает готовый `api_token` из env. Реальные API чаще
выдают JWT через register/login — тогда токен добывается фикстурами:

```python
@pytest.fixture(scope="session")
def session_user(anonymous_client) -> dict:
    """Регистрирует пользователя на всю сессию; в teardown удаляет аккаунт."""
    payload = registration_payload_factory()
    response = AuthClient(anonymous_client).register(payload)
    assert response.status_code == 201, f"не удалось зарегистрировать пользователя: {response.text}"
    body = response.json()
    yield {
        "id": body["user"]["id"],
        "email": payload["email"],
        "password": payload["password"],
        "token": body["token"],
    }
    delete_account(body["token"])


@pytest.fixture(scope="session")
def http_client(session_user) -> httpx.Client:
    """Сессионный клиент с токеном добытого пользователя."""
    with httpx.Client(
        base_url=settings.base_url,
        headers={"Authorization": f"Bearer {session_user['token']}"},
        timeout=settings.timeout,
    ) as client:
        yield client
```

Правила:

- **`session_user` хранит и креды, и токен** — тесты логина переиспользуют email/password,
  не создавая лишних пользователей.
- **Разрушающие сценарии — только на отдельном `temp_user`** (function-scope): смена
  email, удаление аккаунта, проверка доступа к чужим ресурсам. Сессионного пользователя
  такие тесты сломали бы для остальных:

```python
@pytest.fixture
def temp_user(anonymous_client) -> dict:
    """Свежий пользователь на один тест + собственный httpx.Client с его токеном.
    Teardown не падает, если тест уже удалил аккаунт сам."""
    ...
    yield {"id": ..., "email": ..., "password": ..., "token": ..., "client": client}
    delete_account(token)
    client.close()
```

- **Чужие ресурсы**: пара `created_*` (от сессионного пользователя) + `temp_user` даёт
  тесты «чужое нельзя читать/удалять» (403) без спец-подготовки данных.
- Удаление аккаунта в teardown — отдельной функцией с собственным коротким клиентом
  (`delete_account(token)`), потому что сессионный клиент к моменту teardown уже закрыт.

## Роли (admin/user)

- Самостоятельная регистрация обычно даёт минимальную роль — админские операции
  покрывайте негативами 401/403 уже сейчас, они не требуют админа.
- Для позитивного админского CRUD заведите креды в конфиге и **скипайте, а не падайте**,
  если их не выдали:

```python
class Settings(BaseSettings):
    ...
    admin_email: str = ""
    admin_password: str = ""


@pytest.fixture(scope="session")
def admin_client(anonymous_client) -> httpx.Client:
    if not (settings.admin_email and settings.admin_password):
        pytest.skip("админские креды не заданы (API_TESTS_ADMIN_EMAIL/PASSWORD)")
    response = AuthClient(anonymous_client).login(settings.admin_email, settings.admin_password)
    assert response.status_code == 200, f"логин админа не удался: {response.text}"
    ...
```

- Если ролей больше двух — не плодите фикстуры-близнецы, сделайте фабрику
  `client_for_role(role)` поверх общего кода логина.

## Общий (грязный) стенд

Признаки: данными пользуются другие люди/прогоны, в справочниках мусор,
чужие сущности конфликтуют с вашими.

- **Конфликты ресурсов — ретрай с новыми случайными данными**, а не фиксированные
  значения. Проверяйте, что повторяете только по ожидаемой ошибке:

```python
@pytest.fixture
def create_booking(bookings_api, available_room):
    """Чужое бронирование может занять даты комнаты (400 Room is not available) —
    при конфликте пробуем новое случайное окно. Возвращает (payload, booking)."""

    def _create() -> tuple[dict, dict]:
        for _ in range(5):
            payload = _booking_payload(available_room)
            response = bookings_api.create(**payload)
            if response.status_code == 201:
                return payload, response.json()
            assert response.status_code == 400 and "not available" in response.text, response.text
        pytest.fail("не удалось подобрать свободное окно дат за 5 попыток")

    return _create
```

- **Уникальность данных** — случайный суффикс в каждом идентифицирующем поле
  (`qa.{user_name}.{random_int}@example.com`): защищает и от чужих данных,
  и от своих прошлых прогонов, упавших до teardown.
- **Опорные данные берите со стенда, а не хардкодьте**: фикстура находит подходящую
  сущность (например, первую свободную активную комнату) и падает с понятным
  сообщением, если таких нет.
- **Чужой мусор в ответах**: если в списках встречаются сущности с невалидными
  значениями (email вида `test_{{timestamp}}@...`), ослабляйте только конкретное поле
  модели (str вместо EmailStr) и фиксируйте причину комментарием — не отключайте
  `extra="forbid"` целиком.
- Один общий стенд ≠ повод отказаться от контроля: расхождения из-за мусорных данных —
  повод для разговора с владельцем стенда, покажите их пользователю.

## Java-эквиваленты (JUnit 5 + REST Assured / Selenide)

Те же паттерны в терминах Java. Где лежат реализации: сессионный пользователь и
ретрай `createBooking` — в `templates/api-java/` (`BaseTest.java`,
`BookingLifecycleTests.java`; проверены запуском); temp-пользователь — в
`templates/web-java-selenide/` (`ApiAuth.java` + `LoginTests.java`); admin-skip —
сниппет для адаптации, готового теста в шаблонах нет (конфиг-поля уже есть
в `TestConfig` шаблона api-java).

**Сессионный пользователь** — `@BeforeAll`/`@AfterAll` в `BaseTest` вместо
session-scoped фикстуры (реализация: `templates/api-java/.../tests/BaseTest.java`).
Один пользователь на тест-класс: JUnit гоняет классы последовательно, teardown
чистит перед следующим.

```java
@BeforeAll
static void createSessionUser() {
    Response response = new AuthClient().register(registrationPayload());
    assertStatus(response, 201);
    sessionToken = assertContract(response, RegisterResponse.class).token();
}

@AfterAll
static void deleteSessionUser() {
    if (sessionToken != null) new UsersClient(sessionToken).deleteMe();
}
```

**Одноразовый пользователь для разрушающих сценариев** (аналог `temp_user`) —
`@BeforeEach`/`@AfterEach` в конкретном тест-классе: смена email, удаление аккаунта,
доступ к чужим ресурсам не должны трогать сессионного пользователя. Рабочая
реализация живёт в `templates/web-java-selenide/` (`ApiAuth.java` + `LoginTests.java`);
для api-java адаптируйте её на клиентах шаблона (`AuthClient`/`UsersClient`).

```java
private ApiAuth.TestUser user;

@BeforeEach
void createUser() { user = ApiAuth.registerUser(); }

@AfterEach
void deleteUser() {
    // null-guard: если setup упал, user == null — NPE замаскировал бы исходную ошибку;
    // deleteAccount не падает, если тест уже удалил аккаунт сам
    if (user != null) ApiAuth.deleteAccount(user.token());
}
```

**Роли со skip вместо падения** — `Assumptions.assumeTrue`: без админских кредов
тест помечается skipped, а не failed. Готового админского теста в шаблонах нет
(на учебном стенде нет админских кредов) — сниппет ниже адаптируйте под свой API;
конфиг-поля `TestConfig.adminEmail()`/`adminPassword()` (env
`API_TESTS_ADMIN_EMAIL`/`API_TESTS_ADMIN_PASSWORD`) в api-java уже есть.

```java
@BeforeAll
static void loginAsAdmin() {
    Assumptions.assumeTrue(!TestConfig.adminEmail().isBlank(),
            "админские креды не заданы (API_TESTS_ADMIN_EMAIL/PASSWORD)");
    Response response = new AuthClient().login(TestConfig.adminEmail(), TestConfig.adminPassword());
    assertStatus(response, 200);
    adminToken = assertContract(response, LoginResponse.class).token();
}
```

**Ретрай конфликтов общего стенда** — цикл с новыми случайными данными; повторяем
только по ожидаемой ошибке, всё остальное — падение (см. `createBooking`
в `BookingLifecycleTests.java`):

```java
private Booking createBooking(BookingsClient client) {
    for (int attempt = 0; attempt < 5; attempt++) {
        Response response = client.create(bookingPayload(hotelId, roomId, roomTypeId));
        if (response.statusCode() == 201) return assertContract(response, Booking.class);
        assertThat(response.statusCode()).isEqualTo(400);
        assertThat(response.asString()).contains("not available");
    }
    return fail("не удалось подобрать свободное окно дат за 5 попыток");
}
```

**Уникальные данные** — `ThreadLocalRandom` в `TestDataFactory` (двойной случайный
суффикс в email) — аналог faker-фабрик; **асинхронные операции** — Awaitility
(`await().atMost(...).untilAsserted(...)`) — аналог `wait_until`, `Thread.sleep` запрещён.
