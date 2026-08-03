from fastapi import APIRouter

from .auth import router as _auth_router

users_v1_router = APIRouter(prefix="/v1")
"""Агрегатор роутеров HTTP API версии v1 bounded context Users.

Объединяет HTTP-роутеры версии v1 контекста Users в единый роутер
с префиксом ``/v1``, который подключается к приложению в Composition Root.

Notes
-----
Подключает подроутер ``auth`` с тегом ``authorization``, предоставляющий
эндпоинт регистрации пользователя ``POST /v1/auth/register``.
"""

users_v1_router.include_router(_auth_router)

__all__ = ["users_v1_router"]
