"""Pydantic-модели ответов ресурса /users (пример — замените на свой ресурс).
Контракт: extra='forbid' ловит недокументированные поля, обязательность
и типы проверяются автоматически. Общие модели (ApiError) — в models/common.py."""
from pydantic import BaseModel, ConfigDict, EmailStr


class UserResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    email: EmailStr
    age: int
