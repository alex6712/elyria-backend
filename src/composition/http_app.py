from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any, AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.composition.settings import get_settings
from src.presentation.http.root import api_root_router

_settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, Any]:
    """Менеджер срока службы FastAPI-приложения.

    Используется для менеджмента самого приложения в процессе
    его работы.

    Parameters
    ----------
    app : FastAPI
        Объект приложения для менеджмента.

    Yields
    ------
    None
        При успешном выполнении ничего не возвращает.
    """
    app.state.startup_at = datetime.now(timezone.utc)

    yield


elyria_http_app = FastAPI(
    title=_settings.APP_NAME,
    summary=_settings.APP_SUMMARY,
    description=_settings.APP_DESCRIPTION,
    version=_settings.APP_VERSION,
    openapi_tags=[
        {"name": "root", "description": "Получение информации о **приложении**."},
        {
            "name": "authorization",
            "description": "Операции **регистрации** и **аутентификации**.",
        },
        {
            "name": "couples",
            "description": "Операции с **парами** между пользователями приложения.",
        },
        {"name": "users", "description": "Операции с **пользователями** приложения."},
        {
            "name": "media-files",
            "description": "Операции с **медиафайлами**: загрузка, скачивание, presigned URLs.",
        },
        {
            "name": "media-albums",
            "description": "Операции с **медиаальбомами**: создание, получение, привязка файлов.",
        },
        {"name": "notes", "description": "Операции с пользовательскими **заметками**."},
        {
            "name": "dashboard",
            "description": "Операции по получению агрегированных данных для **главной страницы** приложения.",
        },
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
