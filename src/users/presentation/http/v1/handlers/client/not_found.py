from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from src.shared.presentation.http import APICode
from src.shared.presentation.http.schemas import StandardResponse
from src.users.application.exceptions import (
    IdentityNotFoundError,
    ProfileNotFoundError,
    SessionNotFoundError,
)


async def _profile_not_found_error_handler(
    _request: Request, exc: Exception
) -> JSONResponse:
    """Обработать исключение ProfileNotFoundError.

    Возвращает клиенту ответ с HTTP 404 Not Found, если профиль
    с указанным идентификатором отсутствует в системе.

    Parameters
    ----------
    _request : Request
        Объект запроса FastAPI, содержащий информацию о входящем
        HTTP-запросе (не используется).
    exc : Exception
        Экземпляр исключения, из которого получается текст сообщения
        об ошибке.

    Returns
    -------
    JSONResponse
        Ответ с ошибкой 404.
    """
    return JSONResponse(
        content=StandardResponse(
            code=APICode.RESOURCE_NOT_FOUND, detail=str(exc)
        ).model_dump(mode="json"),
        status_code=status.HTTP_404_NOT_FOUND,
    )


async def _session_not_found_error_handler(
    _request: Request, exc: Exception
) -> JSONResponse:
    """Обработать исключение SessionNotFoundError.

    Возвращает клиенту ответ с HTTP 404 Not Found, если сессия
    с указанным идентификатором отсутствует либо сохранённый хеш
    секрета не соответствует хешу переданного токена (защита
    от кражи токена).

    Parameters
    ----------
    _request : Request
        Объект запроса FastAPI, содержащий информацию о входящем
        HTTP-запросе (не используется).
    exc : Exception
        Экземпляр исключения, из которого получается текст сообщения
        об ошибке.

    Returns
    -------
    JSONResponse
        Ответ с ошибкой 404.
    """
    return JSONResponse(
        content=StandardResponse(
            code=APICode.RESOURCE_NOT_FOUND, detail=str(exc)
        ).model_dump(mode="json"),
        status_code=status.HTTP_404_NOT_FOUND,
    )


async def _identity_not_found_error_handler(
    _request: Request, exc: Exception
) -> JSONResponse:
    """Обработать исключение IdentityNotFoundError.

    Возвращает клиенту ответ с HTTP 404 Not Found, если учётная
    запись, указанная в access-токене, отсутствует в системе
    (например, была удалена после выпуска токена).

    Parameters
    ----------
    _request : Request
        Объект запроса FastAPI, содержащий информацию о входящем
        HTTP-запросе (не используется).
    exc : Exception
        Экземпляр исключения, из которого получается текст сообщения
        об ошибке.

    Returns
    -------
    JSONResponse
        Ответ с ошибкой 404.
    """
    return JSONResponse(
        content=StandardResponse(
            code=APICode.RESOURCE_NOT_FOUND, detail=str(exc)
        ).model_dump(mode="json"),
        status_code=status.HTTP_404_NOT_FOUND,
    )


def register(app: FastAPI) -> None:
    """Зарегистрировать обработчики исключений на приложении.

    Parameters
    ----------
    app : FastAPI
        Экземпляр FastAPI-приложения, на который регистрируются
        обработчики.
    """
    app.add_exception_handler(ProfileNotFoundError, _profile_not_found_error_handler)
    app.add_exception_handler(SessionNotFoundError, _session_not_found_error_handler)
    app.add_exception_handler(IdentityNotFoundError, _identity_not_found_error_handler)
