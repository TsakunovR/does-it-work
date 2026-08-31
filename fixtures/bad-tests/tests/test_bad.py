"""Нарушения правил линтера — по одному на правило. Код не предназначен для запуска."""
import time

import allure
import httpx
import pytest
import requests
from pydantic import BaseModel, ConfigDict

TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.payload.signature"  # secret
PASSWORD = "sup3rsecret-password"  # secret

counter = 0


class LooseUser(BaseModel):
    model_config = ConfigDict(extra="ignore")  # weak-contract
    id: str


def test_without_any_check(users_api):  # no-assert, no-severity
    users_api.list()


def test_only_status(users_api):  # weak-assert, no-severity
    response = users_api.list()
    assert response.status_code == 200


def test_sleeps_and_calls_http_directly():  # sleep, http-in-test, hardcoded-url, no-severity
    requests.get("https://staging.internal.example.org/users")
    time.sleep(3)
    httpx.get("https://staging.internal.example.org/health")
    assert True


def test_hardcoded_reference_data(users_api):  # hardcoded-id, no-severity
    response = users_api.get("7c9e6679-7425-40de-944b-e07fc1f90ae7")
    assert response.status_code == 200


def test_waits_for_network_idle(page):  # networkidle, fragile-xpath, no-severity
    page.wait_for_load_state("networkidle")
    page.locator("xpath=//div[2]/span[1]").click()
    assert page.title()


@pytest.mark.xfail(reason="Баг API: список пустой")
def test_known_bug(users_api):  # no-severity
    assert users_api.list().json() == []


@pytest.mark.flaky
def test_quarantined(users_api):
    assert users_api.list().status_code == 200


@allure.severity(allure.severity_level.NORMAL)
def test_writes_global_state(users_api):  # shared-state
    global counter
    counter += 1
    assert counter == 1
