"""Заглушка API для проверки шаблонов скилла без живого стенда.

Реализует ровно тот контракт, на который написан `templates/api-python`
(ресурс /users + /health + Bearer-авторизация). Нужна для двух вещей:

1. CI скилла (`.github/workflows/templates-smoke.yml`) гоняет против неё
   api-python целиком — шаблоны не могут молча протухнуть.
2. Обучение и демо: ученик поднимает заглушку локально и видит зелёный прогон,
   не имея доступа к стенду.

Запуск:
    uv run --with 'fastapi[standard]' uvicorn main:app --port 8000
    # или: pip install -r requirements.txt && uvicorn main:app --port 8000

Токен по умолчанию — `secret-token` (совпадает с дефолтом config.py шаблона).
Данные живут в памяти процесса: рестарт = чистый стенд.
"""
import os
import uuid

from fastapi import FastAPI, Header, HTTPException, Response
from pydantic import BaseModel, EmailStr, Field

API_TOKEN = os.getenv("STUB_API_TOKEN", "secret-token")

app = FastAPI(title="does-it-work stub API", version="1.0.0")

_users: dict[str, dict] = {}


class UserIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    age: int = Field(ge=0, le=150)


def require_token(authorization: str | None) -> None:
    """401 с телом {"detail": ...} — контракт models/common.py::ApiError.

    Сознательно не используем HTTPBearer: он отдаёт 403 вместо 401,
    а шаблонный тест авторизации ожидает именно 401.
    """
    if authorization != f"Bearer {API_TOKEN}":
        raise HTTPException(status_code=401, detail="Требуется авторизация")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/users")
def list_users(authorization: str | None = Header(default=None)) -> list[dict]:
    require_token(authorization)
    return list(_users.values())


@app.post("/users", status_code=201)
def create_user(payload: UserIn, authorization: str | None = Header(default=None)) -> dict:
    require_token(authorization)
    user = {"id": str(uuid.uuid4()), **payload.model_dump()}
    _users[user["id"]] = user
    return user


@app.get("/users/{user_id}")
def get_user(user_id: str, authorization: str | None = Header(default=None)) -> dict:
    require_token(authorization)
    if user_id not in _users:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return _users[user_id]


@app.delete("/users/{user_id}", status_code=204)
def delete_user(user_id: str, authorization: str | None = Header(default=None)) -> Response:
    require_token(authorization)
    if user_id not in _users:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    del _users[user_id]
    return Response(status_code=204)
