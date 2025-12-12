import argparse
from http import HTTPStatus

import uvicorn
from fastapi import FastAPI, Request, Response
from pydantic import BaseModel

app = FastAPI()

# Состояние мока для управления ответами
mock_state = {"auth_status": HTTPStatus.OK, "action_status": HTTPStatus.OK}


class MockState(BaseModel):
    auth_status: int = HTTPStatus.OK
    action_status: int = HTTPStatus.OK


@app.post("/_control/state")
def set_state(state: MockState):
    global mock_state
    mock_state["auth_status"] = state.auth_status
    mock_state["action_status"] = state.action_status
    return {"status": "updated", "current": mock_state}


@app.post("/auth")
def auth(request: Request, response: Response):
    print(f"Mock received /auth call. Returning {mock_state['auth_status']}")
    response.status_code = mock_state["auth_status"]
    return {"status": "mocked_auth"}


@app.post("/doAction")
def do_action(request: Request, response: Response):
    print(f"Mock received /doAction call. Returning {mock_state['action_status']}")
    response.status_code = mock_state["action_status"]
    return {"status": "mocked_action"}


def start_server(port=8888):
    uvicorn.run(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8888)
    args = parser.parse_args()
    start_server(args.port)
