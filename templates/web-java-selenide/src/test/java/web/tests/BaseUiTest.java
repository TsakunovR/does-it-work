package web.tests;

import com.codeborne.selenide.Configuration;
import com.codeborne.selenide.logevents.SelenideLogger;
import io.qameta.allure.Allure;
import io.qameta.allure.selenide.AllureSelenide;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Tag;
import web.api.ApiAuth;
import web.config.WebConfig;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;

import static com.codeborne.selenide.Selenide.closeWebDriver;
import static com.codeborne.selenide.Selenide.executeJavaScript;
import static com.codeborne.selenide.Selenide.open;

/**
 * База UI-тестов: конфигурация Selenide + Allure-листенер
 * (шаги, скриншоты и page source при падении — из коробки).
 */
@Tag("e2e")
public abstract class BaseUiTest {

    @BeforeAll
    static void configure() {
        Configuration.baseUrl = WebConfig.baseUrl();
        Configuration.headless = WebConfig.headless();
        Configuration.browserSize = "1440x900";
        Configuration.timeout = 10_000;
        SelenideLogger.addListener("AllureSelenide",
                new AllureSelenide().screenshots(true).savePageSource(true));
        writeAllureEnvironment();
    }

    @AfterEach
    void tearDownBrowser() {
        closeWebDriver();
    }

    /**
     * Логин через API в обход UI-формы (аналог фикстуры authorized_page из
     * playwright-каркаса): фронт хранит сессию в localStorage под ключом
     * booking_user — открываем базовую страницу и кладём токен туда.
     * Сама форма логина проверяется отдельными тестами (LoginTests).
     */
    protected void loginViaApi(ApiAuth.TestUser user) {
        Allure.step("Авторизуемся через API в обход формы логина: " + user.email(), () -> {
            open("/");
            executeJavaScript("localStorage.setItem('booking_user', arguments[0])",
                    user.storageValue());
        });
    }

    /**
     * environment.properties: в отчёте видно, против какого стенда гоняли.
     * categories.json: группировка падений в Allure (элементы/браузер/сеть).
     */
    private static void writeAllureEnvironment() {
        Path results = Path.of("target", "allure-results");
        try {
            Files.createDirectories(results);
            Files.writeString(results.resolve("environment.properties"),
                    "BASE_URL=" + WebConfig.baseUrl() + "\n"
                            + "JAVA=" + System.getProperty("java.version") + "\n"
                            + "MODE=web-e2e\n");
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
