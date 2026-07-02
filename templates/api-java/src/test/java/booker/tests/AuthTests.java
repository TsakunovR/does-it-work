package booker.tests;

import booker.clients.AuthClient;
import booker.clients.UsersClient;
import booker.models.LoginResponse;
import booker.models.RegisterResponse;
import booker.models.UserProfile;
import io.qameta.allure.Feature;
import io.qameta.allure.Severity;
import io.qameta.allure.SeverityLevel;
import io.qameta.allure.Story;
import io.restassured.response.Response;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.Test;

import java.util.HashMap;
import java.util.Map;

import static booker.utils.ApiAssertions.assertContract;
import static booker.utils.ApiAssertions.assertError;
import static booker.utils.ApiAssertions.assertStatus;
import static booker.utils.TestDataFactory.registrationPayload;
import static org.assertj.core.api.Assertions.assertThat;

@Tag("critical")
@Feature("Авторизация")
class AuthTests extends BaseTest {

    private final AuthClient authClient = new AuthClient();

    /** Токен пользователя, созданного тестом, — для гарантированной очистки в teardown. */
    private String createdUserToken;

    /**
     * Очистка в teardown, а не в конце теста: выполняется и при упавшем ассерте.
     * deleteMe() не проверяет статус — не упадёт, если аккаунт уже удалён.
     */
    @AfterEach
    void deleteCreatedUser() {
        if (createdUserToken != null) {
            new UsersClient(createdUserToken).deleteMe();
            createdUserToken = null;
        }
    }

    @Test
    @Tag("smoke")
    @Story("Регистрация")
    @DisplayName("Регистрация нового пользователя: 201, токен и роль USER")
    @Severity(SeverityLevel.BLOCKER)
    void registerNewUser() {
        Map<String, Object> payload = registrationPayload();

        Response response = authClient.register(payload);

        assertStatus(response, 201);
        // Токен для teardown — до проверки контракта: упавший контракт не должен
        // оставить созданного пользователя на стенде
        createdUserToken = response.jsonPath().getString("token");
        RegisterResponse body = assertContract(response, RegisterResponse.class);
        assertThat(body.token()).as("в ответе нет JWT-токена").isNotBlank();
        assertThat(body.user().email())
                .as("email в ответе должен совпадать с отправленным").isEqualTo(payload.get("email"));
        assertThat(body.user().role())
                .as("самостоятельная регистрация должна давать роль USER").isEqualTo("USER");
    }

    @Test
    @Tag("negative")
    @Story("Регистрация")
    @DisplayName("Регистрация без email: 400 с телом ошибки")
    @Severity(SeverityLevel.NORMAL)
    void registerWithoutEmail() {
        Map<String, Object> payload = new HashMap<>(registrationPayload());
        payload.remove("email");

        assertError(authClient.register(payload), 400);
    }

    @Test
    @Tag("negative")
    @Story("Регистрация")
    @DisplayName("Регистрация с неверным секретным кодом: 403")
    @Severity(SeverityLevel.CRITICAL)
    void registerWithWrongSecretCode() {
        Map<String, Object> payload = new HashMap<>(registrationPayload());
        payload.put("secret_code", "WRONG-CODE");

        assertError(authClient.register(payload), 403);
    }

    @Test
    @Tag("smoke")
    @Story("Логин")
    @DisplayName("Логин с валидными кредами: 200, токен и данные пользователя")
    @Severity(SeverityLevel.BLOCKER)
    void loginWithValidCredentials() {
        Response response = authClient.login(
                (String) sessionPayload.get("email"), (String) sessionPayload.get("password"));

        assertStatus(response, 200);
        LoginResponse body = assertContract(response, LoginResponse.class);
        assertThat(body.token()).as("в ответе нет JWT-токена").isNotBlank();
        assertThat(body.user().id()).isEqualTo(sessionUserId);
    }

    @Test
    @Tag("negative")
    @Story("Логин")
    @DisplayName("Логин с неверным паролем: 401")
    @Severity(SeverityLevel.CRITICAL)
    void loginWithWrongPassword() {
        Response response = authClient.login((String) sessionPayload.get("email"), "wrong-password");

        assertError(response, 401);
    }

    @Test
    @Story("Профиль")
    @DisplayName("GET /users/me возвращает профиль текущего пользователя")
    @Severity(SeverityLevel.CRITICAL)
    void getOwnProfile() {
        Response response = new UsersClient(sessionToken).getMe();

        assertStatus(response, 200);
        UserProfile profile = assertContract(response, UserProfile.class);
        assertThat(profile.id()).isEqualTo(sessionUserId);
        assertThat(profile.email()).isEqualTo(sessionPayload.get("email"));
    }

    @Test
    @Tag("negative")
    @Story("Профиль")
    @DisplayName("Профиль без токена: 401")
    @Severity(SeverityLevel.CRITICAL)
    void profileWithoutToken() {
        assertError(new UsersClient(null).getMe(), 401);
    }
}
