from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any, AsyncGenerator

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
from src.composition.paths import BASE_DIR
from src.composition.settings import get_settings
from src.composition.signature_keys import get_signature_keys
from src.presentation.http.root import api_root_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, Any]:
    """Менеджер срока службы FastAPI-приложения.

    Выполняет инициализацию и освобождение глобальных ресурсов приложения.

    Во время запуска:

    * фиксирует время старта приложения;
    * загружает и кеширует ``.env``;
    * загружает и кеширует пару ключей подписи JWT.

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
    app.state.startup_at = datetime.now(timezone.utc)

    get_settings()
    get_signature_keys()

    yield


elyria_http_app = FastAPI(
    title=APP_NAME,
    summary=APP_SUMMARY,
    description=APP_DESCRIPTION,
    version=APP_VERSION,
    openapi_tags=[
        {"name": "root", "description": "Получение информации о **приложении**."}
    ],
    lifespan=lifespan,
    contact={"name": ADMIN_NAME, "email": ADMIN_EMAIL},
)

elyria_http_app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

elyria_http_app.include_router(api_root_router)

elyria_http_app.mount(
    "/",
    StaticFiles(
        directory=BASE_DIR / "src" / "presentation" / "http" / "static", html=True
    ),
    name="static",
)
