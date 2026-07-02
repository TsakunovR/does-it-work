package web.tests;

import io.qameta.allure.Feature;
import io.qameta.allure.Severity;
import io.qameta.allure.SeverityLevel;
import io.qameta.allure.Story;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.Test;
import web.api.ApiAuth;
import web.pages.LoginPage;

import static com.codeborne.selenide.Condition.visible;
import static com.codeborne.selenide.Selenide.executeJavaScript;
import static com.codeborne.selenide.Selenide.webdriver;
import static com.codeborne.selenide.WebDriverConditions.urlContaining;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertNull;

@Tag("critical")
@Feature("Авторизация")
@Story("Форма логина")
class LoginTests extends BaseUiTest {

    private ApiAuth.TestUser user;

    @BeforeEach
    void createUser() {
        user = ApiAuth.registerUser();
    }

    @AfterEach
    void deleteUser() {
        // null-guard: если createUser() упал, user == null — NPE здесь замаскировал бы
        // исходную ошибку подготовки
        if (user != null) {
            ApiAuth.deleteAccount(user.token());
            user = null;
        }
    }

    @Test
    @Tag("smoke")
    @DisplayName("Успешный логин ведёт в каталог отелей и сохраняет сессию")
    @Severity(SeverityLevel.BLOCKER)
    void loginSuccess() {
        LoginPage login = new LoginPage().openPage();

        login.login(user.email(), user.password());

        webdriver().shouldHave(urlContaining("/hotels"));
        String stored = executeJavaScript("return localStorage.getItem('booking_user')");
        assertNotNull(stored, "после логина нет booking_user в localStorage");
    }

    @Test
    @Tag("negative")
    @DisplayName("Логин с неверным паролем не пускает в систему")
    @Severity(SeverityLevel.CRITICAL)
    void loginWithWrongPassword() {
        LoginPage login = new LoginPage().openPage();

        login.login(user.email(), "wrong-password-123");

        // Сначала ждём сообщение об ошибке — это гарантия, что ответ сервера обработан
        // и поздний редирект уже не случится; только потом проверяем URL и сессию.
        login.errorMessage.shouldBe(visible);
        webdriver().shouldHave(urlContaining("/login"));
        String stored = executeJavaScript("return localStorage.getItem('booking_user')");
        assertNull(stored, "сессия не должна создаваться при неверном пароле");
    }
}
