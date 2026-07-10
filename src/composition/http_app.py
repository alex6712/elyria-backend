from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any, AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.composition.settings import get_settings
from src.composition.signature_keys import get_signature_keys
from src.presentation.http.root import api_root_router

_settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, Any]:
    """Менеджер срока службы FastAPI-приложения.

    Выполняет инициализацию и освобождение глобальных ресурсов приложения.

    Во время запуска:

    * фиксирует время старта приложения;
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

    get_signature_keys()

    yield


elyria_http_app = FastAPI(
    title=_settings.APP_NAME,
    summary=_settings.APP_SUMMARY,
    description=_settings.APP_DESCRIPTION,
    version=_settings.APP_VERSION,
    openapi_tags=[
        {"name": "root", "description": "Получение информации о **приложении**."}
    ],
    lifespan=lifespan,
    contact={"name": _settings.ADMIN_NAME, "email": _settings.ADMIN_EMAIL},
)

elyria_http_app.add_middleware(
    CORSMiddleware,
    allow_origins=_settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

elyria_http_app.include_router(api_root_router)
