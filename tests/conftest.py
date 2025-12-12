import os
import subprocess
import sys
import time
from http import HTTPStatus

import httpx
import pytest
from dotenv import load_dotenv

from api_actions.api_client import ApiClient

# Загружаем переменные из .env
load_dotenv()

# Конфигурация из переменных окружения
MOCK_PORT = int(os.getenv("MOCK_PORT", 8888))
MOCK_HOST = os.getenv("MOCK_HOST", "localhost")
APP_URL = os.getenv("APP_URL", "http://localhost:8080")

MOCK_BASE_URL = f"http://{MOCK_HOST}:{MOCK_PORT}"
MOCK_CONTROL_URL = f"{MOCK_BASE_URL}/_control/state"


@pytest.fixture(scope="session", autouse=True)
def mock_server():
    """Запускает мок-сервер перед тестами и останавливает после."""
    # Путь к скрипту мока
    mock_script = os.path.join(os.path.dirname(__file__), "mock_server.py")

    # Запускаем сервер как отдельный процесс
    proc = subprocess.Popen([sys.executable, mock_script, "--port", str(MOCK_PORT)])

    # Ждем пока сервер поднимется
    timeout = 10
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            httpx.get(f"{MOCK_BASE_URL}/openapi.json")
            break
        except (httpx.ConnectError, httpx.TimeoutException):
            time.sleep(0.5)
        except Exception:
            # На случай других ошибок
            time.sleep(0.5)
    else:
        proc.kill()
        raise RuntimeError("Mock server failed to start")

    yield

    # Останавливаем сервер
    proc.terminate()
    proc.wait()


@pytest.fixture(autouse=True)
def reset_mock():
    """Сбрасывает состояние мока перед каждым тестом."""
    try:
        httpx.post(MOCK_CONTROL_URL, json={"auth_status": HTTPStatus.OK, "action_status": HTTPStatus.OK})
    except (httpx.ConnectError, httpx.TimeoutException):
        pass  # Если сервер упал, другие тесты это покажут


@pytest.fixture
def api_client():
    """Фикстура для HTTP клиента."""
    api_key = os.getenv("VALID_API_KEY", "qazWSXedc")
    return ApiClient(APP_URL, api_key=api_key)
