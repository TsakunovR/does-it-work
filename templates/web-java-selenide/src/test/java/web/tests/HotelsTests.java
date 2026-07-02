package web.tests;

import io.qameta.allure.Feature;
import io.qameta.allure.Severity;
import io.qameta.allure.SeverityLevel;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.Test;
import web.api.ApiAuth;
import web.pages.HotelsPage;

import static com.codeborne.selenide.CollectionCondition.sizeGreaterThan;
import static com.codeborne.selenide.Condition.visible;

/** Авторизованная зона: вход через API в обход формы логина (loginViaApi в BaseUiTest). */
@Tag("critical")
@Feature("Каталог отелей")
class HotelsTests extends BaseUiTest {

    private ApiAuth.TestUser user;

    @BeforeEach
    void createUser() {
        user = ApiAuth.registerUser();
    }

    @AfterEach
    void deleteUser() {
        // null-guard: если createUser() упал, не маскируем исходную ошибку NPE в teardown
        if (user != null) {
            ApiAuth.deleteAccount(user.token());
            user = null;
        }
    }

    @Test
    @Tag("smoke")
    @DisplayName("Каталог отелей открывается после логина через API (в обход UI-формы)")
    @Severity(SeverityLevel.BLOCKER)
    void hotelsListVisibleAfterApiLogin() {
        loginViaApi(user);

        HotelsPage hotels = new HotelsPage().openPage();

        hotels.heading.shouldBe(visible);
        hotels.hotelNames.shouldHave(sizeGreaterThan(0));
        hotels.hotelNames.first().shouldBe(visible);
    }
}
