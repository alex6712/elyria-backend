from fastapi import FastAPI

from src.users.presentation.http.v1.handlers.client.bad_request import (
    register as _register_bad_request_handlers,
)
from src.users.presentation.http.v1.handlers.client.conflict import (
    register as _register_conflict_handlers,
)
from src.users.presentation.http.v1.handlers.client.forbidden import (
    register as _register_forbidden_handlers,
)
from src.users.presentation.http.v1.handlers.client.not_found import (
    register as _register_not_found_handlers,
)
from src.users.presentation.http.v1.handlers.client.unauthorized import (
    register as _register_unauthorized_handlers,
)
from src.users.presentation.http.v1.handlers.client.unprocessable_content import (
    register as _register_unprocessable_content_handlers,
)


def register_exception_handlers(app: FastAPI) -> None:
    """Зарегистрировать обработчики исключений bounded context Users.

    Регистрирует обработчики доменных и прикладных исключений
    контекста Users: 400 (скомпрометированный пароль), 401 (ошибки
    аутентификации и невалидные сессии), 403 (неактивный пользователь),
    404 (сессия не найдена), 409 (занятый username) и 422 (ошибки
    валидации объект-значений).

    Parameters
    ----------
    app : FastAPI
        Экземпляр FastAPI-приложения, на который регистрируются
        обработчики.
    """
    _register_bad_request_handlers(app)
    _register_unauthorized_handlers(app)
    _register_forbidden_handlers(app)
    _register_not_found_handlers(app)
    _register_conflict_handlers(app)
    _register_unprocessable_content_handlers(app)


__all__ = ["register_exception_handlers"]
