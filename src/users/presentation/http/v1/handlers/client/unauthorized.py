from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from src.shared.presentation.http import APICode
from src.shared.presentation.http.schemas import StandardResponse
from src.users.application.exceptions import IncorrectUsernameOrPasswordError
from src.users.domain.exceptions import SessionExpiredError, SessionRevokedError
from src.users.presentation.http.exceptions import (
    AccessTokenMissingError,
    RefreshTokenMissingError,
)


async def _access_token_missing_error_handler(
    _request: Request, exc: Exception
) -> JSONResponse:
    """Обработать исключение AccessTokenMissingError.

    Возвращает клиенту ответ с HTTP 401 Unauthorized, если при
    завершении сессии заголовок ``Authorization`` с Bearer-схемой
    отсутствует во входящем запросе либо имеет некорректный формат.

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
        Ответ с ошибкой 401.
    """
    return JSONResponse(
        content=StandardResponse(
            code=APICode.TOKEN_NOT_PASSED, detail=str(exc)
        ).model_dump(mode="json"),
        status_code=status.HTTP_401_UNAUTHORIZED,
    )


async def _refresh_token_missing_error_handler(
    _request: Request, exc: Exception
) -> JSONResponse:
    """Обработать исключение RefreshTokenMissingError.

    Возвращает клиенту ответ с HTTP 401 Unauthorized, если при
    обновлении пары токенов cookie с refresh-токеном отсутствует
    во входящем запросе.

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
        Ответ с ошибкой 401.
    """
    return JSONResponse(
        content=StandardResponse(
            code=APICode.TOKEN_NOT_PASSED, detail=str(exc)
        ).model_dump(mode="json"),
        status_code=status.HTTP_401_UNAUTHORIZED,
    )


async def _incorrect_username_or_password_error_handler(
    _request: Request, exc: Exception
) -> JSONResponse:
    """Обработать исключение IncorrectUsernameOrPasswordError.

    Возвращает клиенту ответ с HTTP 401 Unauthorized, если при входе
    переданные учётные данные неверны: пользователь с указанным
    ``username`` не найден либо пароль не совпадает с сохранённым хешем.

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
        Ответ с ошибкой 401.
    """
    return JSONResponse(
        content=StandardResponse(
            code=APICode.INCORRECT_USERNAME_PASSWORD, detail=str(exc)
        ).model_dump(mode="json"),
        status_code=status.HTTP_401_UNAUTHORIZED,
    )


async def _session_revoked_error_handler(
    _request: Request, exc: Exception
) -> JSONResponse:
    """Обработать исключение SessionRevokedError.

    Возвращает клиенту ответ с HTTP 401 Unauthorized, если сессия,
    по которой запрошено обновление пары токенов, была принудительно
    завершена (logout).

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
        Ответ с ошибкой 401.
    """
    return JSONResponse(
        content=StandardResponse(
            code=APICode.SESSION_REVOKED, detail=str(exc)
        ).model_dump(mode="json"),
        status_code=status.HTTP_401_UNAUTHORIZED,
    )


async def _session_expired_error_handler(
    _request: Request, exc: Exception
) -> JSONResponse:
    """Обработать исключение SessionExpiredError.

    Возвращает клиенту ответ с HTTP 401 Unauthorized, если срок жизни
    сессии, по которой запрошено обновление пары токенов, истёк,
    хотя переданный refresh-токен может оставаться действительным.

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
        Ответ с ошибкой 401.
    """
    return JSONResponse(
        content=StandardResponse(
            code=APICode.SESSION_EXPIRED, detail=str(exc)
        ).model_dump(mode="json"),
        status_code=status.HTTP_401_UNAUTHORIZED,
    )


def register(app: FastAPI) -> None:
    """Зарегистрировать обработчики исключений на приложении.

    Parameters
    ----------
    app : FastAPI
        Экземпляр FastAPI-приложения, на который регистрируются
        обработчики.
    """
    app.add_exception_handler(
        IncorrectUsernameOrPasswordError, _incorrect_username_or_password_error_handler
    )
    app.add_exception_handler(
        AccessTokenMissingError, _access_token_missing_error_handler
    )
    app.add_exception_handler(
        RefreshTokenMissingError, _refresh_token_missing_error_handler
    )
    app.add_exception_handler(SessionRevokedError, _session_revoked_error_handler)
    app.add_exception_handler(SessionExpiredError, _session_expired_error_handler)
