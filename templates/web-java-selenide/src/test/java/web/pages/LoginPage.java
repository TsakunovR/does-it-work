package web.pages;

import com.codeborne.selenide.SelenideElement;
import io.qameta.allure.Step;

import static com.codeborne.selenide.Selenide.$;
import static com.codeborne.selenide.Selenide.open;

/** Страница логина. */
public class LoginPage {

    public final SelenideElement emailInput = $("#login-email-input");
    public final SelenideElement passwordInput = $("#login-password-input");
    public final SelenideElement submitButton = $("button[type=submit]");
    public final SelenideElement errorMessage = $("#login-error");

    @Step("Открываем страницу логина")
    public LoginPage openPage() {
        open("/login");
        return this;
    }

    @Step("Логинимся через форму: {email}")
    public void login(String email, String password) {
        emailInput.setValue(email);
        passwordInput.setValue(password);
        submitButton.click();
    }
}
