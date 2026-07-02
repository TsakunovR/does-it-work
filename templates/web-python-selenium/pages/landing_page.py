"""Лендинг (главная страница до авторизации)."""
from selenium.webdriver.common.by import By

from pages.base_page import BasePage


class LandingPage(BasePage):
    path = "/"

    # Не xpath по тексту: копирайт меняется чаще вёрстки и ломал бы селектор;
    # текст заголовка проверяется отдельным ассертом в тесте
    TITLE_HEADING = (By.CSS_SELECTOR, "h1")
    LOGIN_BUTTON = (By.ID, "public-login-btn")
