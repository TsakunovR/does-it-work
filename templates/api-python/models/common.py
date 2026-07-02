"""Общие Pydantic-модели, не привязанные к конкретному ресурсу.

ApiError живёт здесь, а не в модели ресурса: utils/assertions.py зависит от неё,
и утилитный слой не должен ломаться при замене примерных ресурсов на свои.
"""
from pydantic import BaseModel, ConfigDict


class ApiError(BaseModel):
    model_config = ConfigDict(extra="forbid")

    detail: str | list
