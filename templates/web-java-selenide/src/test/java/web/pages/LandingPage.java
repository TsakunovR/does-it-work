package web.pages;

import com.codeborne.selenide.SelenideElement;
import io.qameta.allure.Step;

import static com.codeborne.selenide.Selenide.$;
import static com.codeborne.selenide.Selenide.open;

/** Лендинг (главная страница до авторизации). */
public class LandingPage {

    public final SelenideElement titleHeading = $("h1");
    public final SelenideElement loginButton = $("#public-login-btn");

    @Step("Открываем лендинг")
    public LandingPage openPage() {
        open("/");
        return this;
    }
}
