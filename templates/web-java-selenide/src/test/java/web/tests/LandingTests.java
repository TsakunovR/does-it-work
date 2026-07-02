package web.tests;

import io.qameta.allure.Feature;
import io.qameta.allure.Severity;
import io.qameta.allure.SeverityLevel;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.Test;
import web.pages.LandingPage;

import static com.codeborne.selenide.Condition.text;
import static com.codeborne.selenide.Condition.visible;

@Feature("Лендинг")
class LandingTests extends BaseUiTest {

    @Test
    @Tag("smoke")
    @DisplayName("Главная страница открывается: заголовок и кнопка входа видны")
    @Severity(SeverityLevel.BLOCKER)
    void landingOpens() {
        LandingPage landing = new LandingPage().openPage();

        landing.titleHeading.shouldBe(visible).shouldHave(text("Бронируйте отели"));
        landing.loginButton.shouldBe(visible);
    }
}
