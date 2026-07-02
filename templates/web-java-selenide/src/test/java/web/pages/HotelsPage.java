package web.pages;

import com.codeborne.selenide.ElementsCollection;
import com.codeborne.selenide.SelenideElement;
import io.qameta.allure.Step;

import static com.codeborne.selenide.Condition.text;
import static com.codeborne.selenide.Selenide.$;
import static com.codeborne.selenide.Selenide.$$;
import static com.codeborne.selenide.Selenide.open;

/** Каталог отелей (авторизованная зона). */
public class HotelsPage {

    // h1 на странице нет; названия карточек — тоже h2, поэтому ищем заголовок по тексту
    public final SelenideElement heading = $$("h2").findBy(text("Найдите идеальный отель"));
    public final SelenideElement searchInput = $("#hotel-search-input");
    public final ElementsCollection hotelNames = $$("[id^=hotel-card-name-]");

    @Step("Открываем каталог отелей")
    public HotelsPage openPage() {
        open("/hotels");
        return this;
    }
}
