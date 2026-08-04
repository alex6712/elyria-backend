import asyncio
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import UTC, datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from src.composition.app_info import (
    ADMIN_EMAIL,
    ADMIN_NAME,
    APP_DESCRIPTION,
    APP_NAME,
    APP_SUMMARY,
    APP_VERSION,
)
from src.composition.container import build_application_container
from src.composition.engine import build_engine
from src.composition.paths import HTTP_STATIC_FILES_PATH
from src.composition.redis import build_redis_client
from src.composition.settings import get_settings
from src.shared.presentation.http import api_root_router
from src.users.presentation.http.v1.routes import users_v1_router

_settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    """Менеджер срока службы FastAPI-приложения.

    Выполняет инициализацию и освобождение глобальных ресурсов приложения.

    Во время запуска:

    * фиксирует время старта приложения.

    При завершении работы:

    * освобождает пул соединений SQLAlchemy (``dispose``);
    * закрывает асинхронный клиент Redis.

    Если какой-либо ресурс не удалось инициализировать, приложение
    завершит запуск с ошибкой.

    Parameters
    ----------
    app : FastAPI
        Экземпляр FastAPI-приложения.

    Yields
    ------
    None
        Управление передаётся приложению после успешной инициализации
        всех ресурсов.
    """
    app.state.startup_at = datetime.now(UTC)
    app.state.container = build_application_container()

    yield

    _ = await asyncio.gather(build_engine().dispose(), build_redis_client().aclose())


elyria_http_app = FastAPI(
    title=APP_NAME,
    summary=APP_SUMMARY,
    description=APP_DESCRIPTION,
    version=APP_VERSION,
    openapi_tags=[
        {"name": "root", "description": "Получение информации о **приложении**."},
        {
            "name": "auth",
            "description": "Операции **регистрации** и **аутентификации**.",
        },
    ],
    lifespan=lifespan,
    contact={"name": ADMIN_NAME, "email": ADMIN_EMAIL},
)

elyria_http_app.add_middleware(
    CORSMiddleware,
    allow_origins=_settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

elyria_http_app.include_router(api_root_router)
elyria_http_app.include_router(users_v1_router)

elyria_http_app.mount(
    "/", StaticFiles(directory=HTTP_STATIC_FILES_PATH, html=True), name="static"
)
