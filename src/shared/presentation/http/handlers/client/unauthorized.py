from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from src.shared.application.exceptions import (
    TokenExpiredError,
    TokenInvalidError,
    TokenRevokedError,
    TokenSignatureInvalidError,
)
from src.shared.presentation.http import APICode
from src.shared.presentation.http.schemas import StandardResponse


async def _token_expired_error_handler(
    _request: Request, exc: Exception
) -> JSONResponse:
    """Обработать исключение TokenExpiredError.

    Возвращает клиенту ответ с HTTP 401 Unauthorized, если срок
    действия переданного токена истёк, но его подпись действительна.

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
            code=APICode.TOKEN_SIGNATURE_EXPIRED, detail=str(exc)
        ).model_dump(mode="json"),
        status_code=status.HTTP_401_UNAUTHORIZED,
    )


async def _token_signature_invalid_error_handler(
    _request: Request, exc: Exception
) -> JSONResponse:
    """Обработать исключение TokenSignatureInvalidError.

    Возвращает клиенту ответ с HTTP 401 Unauthorized, если подпись
    переданного токена не прошла проверку.

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
            code=APICode.INVALID_TOKEN, detail=str(exc)
        ).model_dump(mode="json"),
        status_code=status.HTTP_401_UNAUTHORIZED,
    )


async def _token_invalid_error_handler(
    _request: Request, exc: Exception
) -> JSONResponse:
    """Обработать исключение TokenInvalidError.

    Возвращает клиенту ответ с HTTP 401 Unauthorized, если в токене
    отсутствуют обязательные утверждения либо нарушен формат данных.

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
            code=APICode.INVALID_TOKEN, detail=str(exc)
        ).model_dump(mode="json"),
        status_code=status.HTTP_401_UNAUTHORIZED,
    )


async def _token_revoked_error_handler(
    _request: Request, exc: Exception
) -> JSONResponse:
    """Обработать исключение TokenRevokedError.

    Возвращает клиенту ответ с HTTP 401 Unauthorized, если токен
    был отозван.

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
            code=APICode.TOKEN_REVOKED, detail=str(exc)
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
    app.add_exception_handler(TokenExpiredError, _token_expired_error_handler)
    app.add_exception_handler(
        TokenSignatureInvalidError, _token_signature_invalid_error_handler
    )
    app.add_exception_handler(TokenInvalidError, _token_invalid_error_handler)
    app.add_exception_handler(TokenRevokedError, _token_revoked_error_handler)
