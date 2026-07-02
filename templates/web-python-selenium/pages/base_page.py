"""Базовый Page Object для Selenium: явные ожидания вместо sleep."""
import allure
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from config import settings


class BasePage:
    path = "/"

    def __init__(self, driver: WebDriver):
        self.driver = driver
        self.wait = WebDriverWait(driver, timeout=settings.timeout)

    def open(self) -> "BasePage":
        with allure.step(f"Открываем {self.path}"):
            self.driver.get(settings.base_url + self.path)
        return self

    def visible(self, locator: tuple):
        """Ждёт видимости элемента и возвращает его — единственный способ
        обращения к элементам, никаких find_element без ожидания."""
        return self.wait.until(EC.visibility_of_element_located(locator))
