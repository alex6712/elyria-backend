from fastapi import FastAPI

from src.shared.presentation.http.handlers.client.conflict import (
    register as _register_conflict_handlers,
)
from src.shared.presentation.http.handlers.client.unprocessable_content import (
    register as _register_unprocessable_content_handlers,
)
from src.shared.presentation.http.handlers.server.internal_server_error import (
    register as _register_internal_server_error_handlers,
)


def register_exception_handlers(app: FastAPI) -> None:
    """Зарегистрировать обработчики общих исключений на приложении.

    Регистрирует обработчики исключений, общих для всех bounded
    contexts: конфликт оптимистичной блокировки (409), ошибки
    валидации запроса (422) и непредвиденные ошибки сервера (500).

    Parameters
    ----------
    app : FastAPI
        Экземпляр FastAPI-приложения, на который регистрируются
        обработчики.
    """
    _register_conflict_handlers(app)
    _register_unprocessable_content_handlers(app)
    _register_internal_server_error_handlers(app)


__all__ = ["register_exception_handlers"]
