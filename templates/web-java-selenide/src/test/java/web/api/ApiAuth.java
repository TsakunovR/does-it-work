package web.api;

import web.config.WebConfig;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import java.util.concurrent.ThreadLocalRandom;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * Подготовка данных через API (stdlib HttpClient — без лишних зависимостей):
 * UI-тесты не должны готовить состояние через UI.
 */
public final class ApiAuth {

    /** Дефолт HttpClient — ждать вечно; ограничиваем из конфига (WEB_TESTS_TIMEOUT_MS),
     *  чтобы зависший API не вешал прогон. */
    private static final Duration TIMEOUT = Duration.ofMillis(WebConfig.timeoutMs());

    private static final HttpClient HTTP = HttpClient.newBuilder()
            .connectTimeout(TIMEOUT)
            .build();
    private static final Pattern TOKEN = Pattern.compile("\"token\"\\s*:\\s*\"([^\"]+)\"");
    /** Объект user в ответе регистрации плоский — скобки не вложены, регэкспа достаточно. */
    private static final Pattern USER = Pattern.compile("\"user\"\\s*:\\s*(\\{[^{}]*})");

    private ApiAuth() {
    }

    public record TestUser(String email, String password, String token, String userJson) {

        /**
         * Значение ключа booking_user в localStorage — так фронт хранит сессию
         * (структура подсмотрена в приложении: {"token": ..., "user": {...}}).
         */
        public String storageValue() {
            return "{\"token\":\"" + token + "\",\"user\":" + userJson + "}";
        }
    }

    /** Регистрирует свежего пользователя, возвращает креды и токен. */
    public static TestUser registerUser() {
        String email = "qa.selenide." + ThreadLocalRandom.current().nextInt(100_000, 999_999)
                + "." + ThreadLocalRandom.current().nextInt(100_000, 999_999) + "@example.com";
        String password = "Qa" + ThreadLocalRandom.current().nextInt(10_000_000, 99_999_999) + "!";
        String body = """
                {"email":"%s","password":"%s","secret_code":"%s"}"""
                .formatted(email, password, WebConfig.secretCode());
        HttpResponse<String> response = send(HttpRequest.newBuilder()
                .uri(URI.create(WebConfig.apiUrl() + "/auth/register"))
                .header("Content-Type", "application/json")
                .timeout(TIMEOUT)
                .POST(HttpRequest.BodyPublishers.ofString(body))
                .build());
        if (response.statusCode() != 201) {
            throw new AssertionError("не удалось зарегистрировать пользователя: " + response.body());
        }
        Matcher token = TOKEN.matcher(response.body());
        if (!token.find()) {
            throw new AssertionError("в ответе регистрации нет токена: " + response.body());
        }
        Matcher user = USER.matcher(response.body());
        if (!user.find()) {
            throw new AssertionError("в ответе регистрации нет объекта user: " + response.body());
        }
        return new TestUser(email, password, token.group(1), user.group(1));
    }

    /** Удаляет аккаунт; не падает, если он уже удалён. */
    public static void deleteAccount(String token) {
        send(HttpRequest.newBuilder()
                .uri(URI.create(WebConfig.apiUrl() + "/users/me"))
                .header("Authorization", "Bearer " + token)
                .timeout(TIMEOUT)
                .DELETE()
                .build());
    }

    private static HttpResponse<String> send(HttpRequest request) {
        try {
            return HTTP.send(request, HttpResponse.BodyHandlers.ofString());
        } catch (Exception e) {
            throw new AssertionError("HTTP-запрос к API не удался: " + e.getMessage(), e);
        }
    }
}
