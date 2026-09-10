from fastapi import APIRouter

from .auth import router as _auth_router
from .profiles import router as _profiles_router
from .users import router as _users_router

users_v1_router = APIRouter(prefix="/v1")
"""Агрегатор роутеров HTTP API версии v1 bounded context Users.

Объединяет HTTP-роутеры версии v1 контекста Users в единый роутер
с префиксом ``/v1``. Подключает подроутеры ``auth`` (тег ``authorization``),
``profiles`` (тег ``profiles``) и ``users`` (тег ``users``).
"""

users_v1_router.include_router(_auth_router)
users_v1_router.include_router(_profiles_router)
users_v1_router.include_router(_users_router)

__all__ = ["users_v1_router"]
