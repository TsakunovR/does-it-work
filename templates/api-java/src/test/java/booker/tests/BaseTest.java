package booker.tests;

import booker.clients.AuthClient;
import booker.clients.UsersClient;
import booker.models.RegisterResponse;
import io.restassured.response.Response;
import org.junit.jupiter.api.AfterAll;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Tag;

import java.util.Map;

import static booker.utils.ApiAssertions.assertContract;
import static booker.utils.ApiAssertions.assertStatus;
import static booker.utils.TestDataFactory.registrationPayload;

/**
 * База e2e-тестов: сессионный пользователь на класс — регистрируется в @BeforeAll,
 * удаляется в @AfterAll. Окружение Allure (environment.properties + categories.json)
 * пишет {@link booker.support.AllureEnvironmentListener} на старте прогона — оно
 * не привязано к этой базе и появляется для любого тест-класса (в т.ч. HealthTests).
 */
@Tag("e2e")
public abstract class BaseTest {

    protected static Map<String, Object> sessionPayload;
    protected static String sessionToken;
    protected static long sessionUserId;

    @BeforeAll
    static void createSessionUser() {
        sessionPayload = registrationPayload();
        Response response = new AuthClient().register(sessionPayload);
        assertStatus(response, 201);
        RegisterResponse body = assertContract(response, RegisterResponse.class);
        sessionToken = body.token();
        sessionUserId = body.user().id();
    }

    @AfterAll
    static void deleteSessionUser() {
        if (sessionToken != null) {
            new UsersClient(sessionToken).deleteMe();
            sessionToken = null;
        }
    }
}
