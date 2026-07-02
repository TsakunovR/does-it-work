package booker.support;

import booker.config.TestConfig;
import org.junit.platform.launcher.TestExecutionListener;
import org.junit.platform.launcher.TestPlan;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;

/**
 * Пишет окружение Allure один раз на старте прогона — независимо от того, какие
 * тест-классы в него попали.
 *
 * <p>environment.properties: в отчёте видно, против какого стенда гоняли.
 * categories.json (копия allure-categories.json): группировка падений в Allure
 * (контракт/сеть/известные баги).
 *
 * <p>Раньше это делал {@code BaseTest.@BeforeAll} — из-за чего одиночный прогон
 * {@code HealthTests} (не наследует BaseTest, авторизация ему не нужна) оставался
 * без окружения. Listener уровня платформы решает это для ЛЮБОГО тест-класса и не
 * требует наследования/авторизации.
 *
 * <p>Регистрируется автоматически через ServiceLoader:
 * {@code src/test/resources/META-INF/services/org.junit.platform.launcher.TestExecutionListener}.
 */
public class AllureEnvironmentListener implements TestExecutionListener {

    @Override
    public void testPlanExecutionStarted(TestPlan testPlan) {
        Path results = Path.of("target", "allure-results");
        try {
            Files.createDirectories(results);
            Files.writeString(results.resolve("environment.properties"),
                    "BASE_URL=" + TestConfig.baseUrl() + "\n"
                            + "JAVA=" + System.getProperty("java.version") + "\n");
            Path categories = Path.of("allure-categories.json");
            if (Files.exists(categories)) {
                Files.copy(categories, results.resolve("categories.json"),
                        StandardCopyOption.REPLACE_EXISTING);
            }
        } catch (IOException e) {
            throw new UncheckedIOException(e);
        }
    }
}
