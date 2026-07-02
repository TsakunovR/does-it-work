package booker.tests;

import booker.clients.UsersClient;
import io.qameta.allure.Feature;
import io.qameta.allure.Severity;
import io.qameta.allure.SeverityLevel;
import io.qameta.allure.Story;
import io.restassured.response.Response;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.Test;

import java.util.Map;

import static org.assertj.core.api.Assertions.assertThat;

/**
 * Известные (подтверждённые) баги RV Booker.
 *
 * <p>В JUnit 5 нет strict-xfail (как pytest.mark.xfail(strict=True) в python-ветке),
 * поэтому известный баг фиксируется идиоматично для JUnit: тест проверяет
 * <b>корректное</b> поведение (то, каким API должен быть после фикса) и потому сейчас
 * падает. Чтобы падение не ломало зелёный прогон, тест помечен {@code @Tag("flaky")} —
 * тот же карантинный тег, что исключается в основном прогоне ({@code excludedGroups=flaky}
 * в pom). Запуск карантина ({@code mvn test -DexcludedGroups=}) прогоняет его: он падает,
 * а сообщение содержит «Баг API: …», по которому Allure относит падение в категорию
 * «Известные баги API (карантин flaky)» из allure-categories.json.
 *
 * <p>Когда баг починят — assertion станет зелёным; тег flaky можно снять и тест
 * переедет в обычный сьют. Так известный баг остаётся исполняемым и самопроверяемым,
 * а не мёртвым комментарием.
 */
@Tag("flaky")
@Feature("Профиль")
@Story("Известные баги")
class KnownBugsTests extends BaseTest {

    @Test
    @Tag("negative")
    @DisplayName("PUT /users/me с невалидным email должен отклоняться (400)")
    @Severity(SeverityLevel.NORMAL)
    void updateProfileWithInvalidEmailIsRejected() {
        // Мутируем e-mail сессионного пользователя намеренно: класс содержит только
        // этот тест, аккаунт всё равно удаляется в BaseTest.@AfterAll — контаминации нет.
        Response response = new UsersClient(sessionToken).updateMe(Map.of("email", "не-почта-invalid"));

        assertThat(response.statusCode())
                .as("Баг API: PUT /users/me принимает невалидный email — вернул %d вместо 400. Тело: %s",
                        response.statusCode(), response.asString())
                .isEqualTo(400);
    }
}
