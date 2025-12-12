import os
from http import HTTPStatus

import allure
import httpx
import pytest

# Конфигурация
VALID_TOKEN = os.getenv("VALID_TOKEN", "A" * 32)
# Для негативных тестов генерируем токены на основе валидного или просто строки
INVALID_TOKEN_LENGTH_SHORT = "A" * 31
INVALID_TOKEN_LENGTH_LONG = "A" * 33
INVALID_TOKEN_CHARS = VALID_TOKEN[:-1] + "!"

MOCK_PORT = os.getenv("MOCK_PORT", "8888")
MOCK_HOST = os.getenv("MOCK_HOST", "localhost")
MOCK_CONTROL_URL = f"http://{MOCK_HOST}:{MOCK_PORT}/_control/state"


@allure.epic("Core Functionality")
@allure.feature("Authentication & Actions")
class TestApp:
    @allure.story("Login")
    @allure.title("Успешный вход в систему (LOGIN)")
    @allure.description("Проверка сценария успешного логина при корректном токене и ответе 200 от внешнего сервиса.")
    def test_login_success(self, api_client):
        # Предварительная очистка сессии на случай, если токен завис
        api_client.send_request(token=VALID_TOKEN, action="LOGOUT")

        with allure.step("Отправить запрос LOGIN с валидным токеном"):
            response = api_client.send_request(token=VALID_TOKEN, action="LOGIN")

        with allure.step("Проверить статус ответа"):
            assert (
                response.status_code == HTTPStatus.OK
            ), f"Expected 200, got {response.status_code}. Body: {response.text}"

        with allure.step("Проверить тело ответа"):
            assert response.json() == {"result": "OK"}

    @allure.story("Login")
    @allure.title("Неуспешный вход (LOGIN) - ошибка внешнего сервиса")
    def test_login_external_fail(self, api_client):
        # Настраиваем мок на ошибку
        httpx.post(MOCK_CONTROL_URL, json={"auth_status": HTTPStatus.INTERNAL_SERVER_ERROR})

        with allure.step("Отправить запрос LOGIN, когда внешний сервис недоступен (500)"):
            response = api_client.send_request(token=VALID_TOKEN, action="LOGIN")

        with allure.step("Проверить, что приложение возвращает ошибку"):
            json_resp = response.json()
            assert json_resp.get("result") == "ERROR", f"Expected result ERROR, got {json_resp}"

    @allure.story("Action")
    @allure.title("Выполнение действия (ACTION) без предварительного логина")
    def test_action_without_login(self, api_client):
        # Генерируем новый уникальный токен, который точно не залогинен
        # Используем валидный формат, но отличный от основного VALID_TOKEN
        unique_token = "B" * 32

        with allure.step("Отправить запрос ACTION без LOGIN"):
            response = api_client.send_request(token=unique_token, action="ACTION")

        with allure.step("Проверить отказ в доступе"):
            json_resp = response.json()
            assert json_resp.get("result") == "ERROR"

    @allure.story("Full Flow")
    @allure.title("Полный сценарий: LOGIN -> ACTION -> LOGOUT -> ACTION")
    def test_full_flow(self, api_client):
        token = "C" * 32

        with allure.step("1. LOGIN"):
            resp = api_client.send_request(token=token, action="LOGIN")
            assert resp.json()["result"] == "OK"

        with allure.step("2. ACTION (должен быть успешен)"):
            resp = api_client.send_request(token=token, action="ACTION")
            assert resp.json()["result"] == "OK"

        with allure.step("3. LOGOUT"):
            resp = api_client.send_request(token=token, action="LOGOUT")
            assert resp.json()["result"] == "OK"

        with allure.step("4. ACTION после LOGOUT (должен быть неуспешен)"):
            resp = api_client.send_request(token=token, action="ACTION")
            assert resp.json().get("result") == "ERROR"

    @allure.story("Validation")
    @allure.title("Невалидная длина токена")
    @pytest.mark.parametrize(
        "token",
        [
            INVALID_TOKEN_LENGTH_SHORT,
            INVALID_TOKEN_LENGTH_LONG,
            "",
        ],
    )
    def test_invalid_token_length(self, api_client, token):
        with allure.step(f"Отправить запрос с длиной токена {len(token)}"):
            response = api_client.send_request(token=token, action="LOGIN")

        with allure.step("Проверить ошибку валидации"):
            # Приложение должно вернуть ошибку
            assert response.json().get("result") == "ERROR"

    @allure.story("Validation")
    @allure.title("Недопустимые символы в токене")
    def test_invalid_token_chars(self, api_client):
        with allure.step("Отправить запрос с недопустимыми символами"):
            response = api_client.send_request(token=INVALID_TOKEN_CHARS, action="LOGIN")

        with allure.step("Проверить ошибку"):
            assert response.json().get("result") == "ERROR"

    @allure.story("Security")
    @allure.title("Доступ без X-Api-Key")
    def test_missing_api_key(self, api_client):
        with allure.step("Отправить запрос без заголовка X-Api-Key"):
            response = api_client.send_request(token=VALID_TOKEN, action="LOGIN", suppress_api_key=True)

        with allure.step("Проверить статус 403/401 или ошибку приложения"):
            assert response.status_code in [
                HTTPStatus.UNAUTHORIZED,
                HTTPStatus.FORBIDDEN,
            ], f"Expected 401/403, got {response.status_code}"

    @allure.story("Security")
    @allure.title("Доступ с неверным X-Api-Key")
    def test_wrong_api_key(self, api_client):
        with allure.step("Отправить запрос с неверным ключом"):
            response = api_client.send_request(token=VALID_TOKEN, action="LOGIN", api_key="wrong")

        with allure.step("Проверить статус 403/401"):
            assert (
                response.status_code in [HTTPStatus.UNAUTHORIZED, HTTPStatus.FORBIDDEN]
                or response.json().get("result") == "ERROR"
            )
