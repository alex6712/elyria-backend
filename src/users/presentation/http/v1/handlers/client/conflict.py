from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from src.shared.presentation.http import APICode
from src.shared.presentation.http.schemas import StandardResponse
from src.users.domain.exceptions import (
    EmailAlreadyExistsError,
    UsernameAlreadyExistsError,
)


async def _username_already_exists_error_handler(
    _request: Request, exc: Exception
) -> JSONResponse:
    """Обработать исключение UsernameAlreadyExistsError.

    Возвращает клиенту ответ с HTTP 409 Conflict в случае, если
    указанный ``username`` уже занят другой учётной записью.

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
        Ответ с ошибкой 409.
    """
    return JSONResponse(
        content=StandardResponse(
            code=APICode.UNIQUE_CONFLICT, detail=str(exc)
        ).model_dump(mode="json"),
        status_code=status.HTTP_409_CONFLICT,
    )


async def _email_already_exists_error_handler(
    _request: Request, exc: Exception
) -> JSONResponse:
    """Обработать исключение EmailAlreadyExistsError.

    Возвращает клиенту ответ с HTTP 409 Conflict в случае, если
    указанный ``email`` уже занят другой учётной записью.

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
        Ответ с ошибкой 409.
    """
    return JSONResponse(
        content=StandardResponse(
            code=APICode.UNIQUE_CONFLICT, detail=str(exc)
        ).model_dump(mode="json"),
        status_code=status.HTTP_409_CONFLICT,
    )


def register(app: FastAPI) -> None:
    """Зарегистрировать обработчики исключений на приложении.

    Parameters
    ----------
    app : FastAPI
        Экземпляр FastAPI-приложения, на который регистрируется
        обработчик.
    """
    app.add_exception_handler(
        UsernameAlreadyExistsError, _username_already_exists_error_handler
    )
    app.add_exception_handler(
        EmailAlreadyExistsError, _email_already_exists_error_handler
    )
