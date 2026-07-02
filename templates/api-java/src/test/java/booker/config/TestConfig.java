package booker.config;

/**
 * Конфигурация окружения — только из переменных окружения API_TESTS_*
 * (та же схема, что и в python-каркасе). Без CLI-флагов: один источник правды.
 */
public final class TestConfig {

    private TestConfig() {
    }

    public static String baseUrl() {
        return env("API_TESTS_BASE_URL", "https://rvtravel.rv-school.ru/api");
    }

    /** Секретный код регистрации (публичный код учебного стенда RVSchool). */
    public static String secretCode() {
        return env("API_TESTS_SECRET_CODE", "TESTCODE2025");
    }

    /** Креды админа для позитивного админского CRUD; пусто — такие тесты скипаются. */
    public static String adminEmail() {
        return env("API_TESTS_ADMIN_EMAIL", "");
    }

    public static String adminPassword() {
        return env("API_TESTS_ADMIN_PASSWORD", "");
    }

    /** Таймаут HTTP (connection + socket), мс. Дефолт REST Assured — бесконечность. */
    public static int timeoutMs() {
        return Integer.parseInt(env("API_TESTS_TIMEOUT_MS", "10000"));
    }

    private static String env(String name, String defaultValue) {
        String value = System.getenv(name);
        return (value == null || value.isBlank()) ? defaultValue : value;
    }
}
