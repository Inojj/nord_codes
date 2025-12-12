import httpx


class ApiClient:
    def __init__(self, base_url, api_key="qazWSXedc"):
        self.base_url = base_url
        self.default_api_key = api_key

    def send_request(self, token: str, action: str, api_key: str = None, suppress_api_key: bool = False):
        """
        Отправляет POST запрос к API.

        :param token: Токен пользователя
        :param action: Действие (LOGIN, ACTION, etc.)
        :param api_key: Явное указание X-Api-Key. Если None, используется дефолтный.
        :param suppress_api_key: Если True, заголовок X-Api-Key не будет отправлен (для тестов безопасности).
        """
        headers = {"Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"}

        if not suppress_api_key:
            if api_key is not None:
                headers["X-Api-Key"] = api_key
            else:
                headers["X-Api-Key"] = self.default_api_key

        data = {"token": token, "action": action}

        with httpx.Client(base_url=self.base_url) as client:
            return client.post("/endpoint", data=data, headers=headers)
