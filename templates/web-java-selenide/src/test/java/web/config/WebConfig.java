package web.config;

/** Конфигурация окружения — только из переменных окружения WEB_TESTS_*. */
public final class WebConfig {

    private WebConfig() {
    }

    public static String baseUrl() {
        return env("WEB_TESTS_BASE_URL", "https://rvtravel.rv-school.ru");
    }

    /** API того же стенда — для подготовки данных и логина в обход UI. */
    public static String apiUrl() {
        return env("WEB_TESTS_API_URL", "https://rvtravel.rv-school.ru/api");
    }

    public static String secretCode() {
        return env("WEB_TESTS_SECRET_CODE", "TESTCODE2025");
    }

    /** Headless-режим браузера; WEB_TESTS_HEADLESS=false — смотреть прогон глазами. */
    public static boolean headless() {
        return Boolean.parseBoolean(env("WEB_TESTS_HEADLESS", "true"));
    }

    /** Connection/socket таймаут HTTP-запросов подготовки данных, мс (дефолт 10 с). */
    public static long timeoutMs() {
        return Long.parseLong(env("WEB_TESTS_TIMEOUT_MS", "10000"));
    }

    private static String env(String name, String defaultValue) {
        String value = System.getenv(name);
        return (value == null || value.isBlank()) ? defaultValue : value;
    }
}
