package booker.clients;

import booker.config.TestConfig;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.datatype.jsr310.JavaTimeModule;
import io.qameta.allure.restassured.AllureRestAssured;
import io.restassured.RestAssured;
import io.restassured.builder.RequestSpecBuilder;
import io.restassured.config.HttpClientConfig;
import io.restassured.config.ObjectMapperConfig;
import io.restassured.config.RestAssuredConfig;
import io.restassured.http.ContentType;
import io.restassured.specification.RequestSpecification;

/**
 * Базовый клиент: единая спецификация запросов с Allure-логированием.
 * Тесты не строят HTTP-запросы сами — только через методы клиентов-наследников.
 * Jackson с настройками по умолчанию падает на неизвестных полях —
 * это наш аналог pydantic extra="forbid": контракт ловит лишние поля.
 */
public abstract class BaseClient {

    private static final ObjectMapper MAPPER = new ObjectMapper().registerModule(new JavaTimeModule());

    private static final RestAssuredConfig CONFIG = RestAssuredConfig.config()
            .objectMapperConfig(ObjectMapperConfig.objectMapperConfig()
                    .jackson2ObjectMapperFactory((type, s) -> MAPPER))
            // Дефолт REST Assured — ждать вечно; ограничиваем connection и socket таймауты,
            // чтобы зависший стенд ронял тест за API_TESTS_TIMEOUT_MS, а не вешал прогон
            .httpClient(HttpClientConfig.httpClientConfig()
                    .setParam("http.connection.timeout", TestConfig.timeoutMs())
                    .setParam("http.socket.timeout", TestConfig.timeoutMs()));

    protected final String token;

    protected BaseClient(String token) {
        this.token = token;
    }

    /**
     * Спецификация запроса; токен добавляется, если клиент авторизованный.
     * Важно: builder.build() возвращает «незапущенную» спецификацию — вызывать
     * .post()/.get() прямо на ней нельзя (NPE assertionClosure), только через given().
     */
    protected RequestSpecification spec() {
        RequestSpecBuilder builder = new RequestSpecBuilder()
                .setBaseUri(TestConfig.baseUrl())
                .setContentType(ContentType.JSON)
                .setConfig(CONFIG)
                .addFilter(new AllureRestAssured());
        if (token != null) {
            builder.addHeader("Authorization", "Bearer " + token);
        }
        return RestAssured.given().spec(builder.build());
    }
}
