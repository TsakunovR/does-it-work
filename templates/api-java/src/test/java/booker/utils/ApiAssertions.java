package booker.utils;

import booker.models.ApiError;
import io.qameta.allure.Allure;
import io.restassured.response.Response;

import static org.assertj.core.api.Assertions.assertThat;

/**
 * Переиспользуемые проверки: Allure-шаг + читаемое сообщение с телом ответа.
 * Аналог utils/assertions.py из python-каркаса.
 */
public final class ApiAssertions {

    private ApiAssertions() {
    }

    public static void assertStatus(Response response, int expected) {
        Allure.step("Статус ответа = " + expected, () ->
                assertThat(response.statusCode())
                        .as("ожидали %d, тело ответа: %s", expected, response.asString())
                        .isEqualTo(expected));
    }

    /** Валидирует тело ответа моделью (Jackson упадёт на неизвестных полях) и возвращает её. */
    public static <T> T assertContract(Response response, Class<T> model) {
        return Allure.step("Контракт ответа: " + model.getSimpleName(), () -> response.as(model));
    }

    /** Негативный кейс одним вызовом: статус + контракт тела ошибки. */
    public static ApiError assertError(Response response, int expected) {
        assertStatus(response, expected);
        ApiError error = assertContract(response, ApiError.class);
        assertThat(error.text()).as("в теле ошибки нет ни error, ни message").isNotBlank();
        return error;
    }
}
