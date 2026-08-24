from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from src.shared.presentation.http import APICode
from src.shared.presentation.http.schemas import StandardResponse
from src.users.domain.exceptions import (
    InvalidAvatarUrlError,
    InvalidAvatarUrlLengthError,
    InvalidDisplayNameLengthError,
    InvalidPasswordLengthError,
    InvalidUsernameFormatError,
    InvalidUsernameLengthError,
)


async def _invalid_avatar_url_length_error_handler(
    _request: Request, exc: Exception
) -> JSONResponse:
    """Обработать исключение InvalidAvatarUrlLengthError.

    Возвращает клиенту ответ с HTTP 422 Unprocessable Content, если
    длина URL изображения аватара выходит за допустимые пределы.

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
        Ответ с ошибкой 422.
    """
    return JSONResponse(
        content=StandardResponse(
            code=APICode.VALIDATION_ERROR, detail=str(exc)
        ).model_dump(mode="json"),
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
    )


async def _invalid_avatar_url_error_handler(
    _request: Request, exc: Exception
) -> JSONResponse:
    """Обработать исключение InvalidAvatarUrlError.

    Возвращает клиенту ответ с HTTP 422 Unprocessable Content, если
    URL изображения аватара не является корректным абсолютным URL
    либо использует схему, отличную от ``http`` и ``https``.

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
        Ответ с ошибкой 422.
    """
    return JSONResponse(
        content=StandardResponse(
            code=APICode.VALIDATION_ERROR, detail=str(exc)
        ).model_dump(mode="json"),
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
    )


async def _invalid_display_name_length_error_handler(
    _request: Request, exc: Exception
) -> JSONResponse:
    """Обработать исключение InvalidDisplayNameLengthError.

    Возвращает клиенту ответ с HTTP 422 Unprocessable Content, если
    длина отображаемого имени выходит за допустимые пределы.

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
        Ответ с ошибкой 422.
    """
    return JSONResponse(
        content=StandardResponse(
            code=APICode.VALIDATION_ERROR, detail=str(exc)
        ).model_dump(mode="json"),
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
    )


async def _invalid_password_length_error_handler(
    _request: Request, exc: Exception
) -> JSONResponse:
    """Обработать исключение InvalidPasswordLengthError.

    Возвращает клиенту ответ с HTTP 422 Unprocessable Content, если
    длина пароля выходит за допустимые пределы.

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
        Ответ с ошибкой 422.
    """
    return JSONResponse(
        content=StandardResponse(
            code=APICode.VALIDATION_ERROR, detail=str(exc)
        ).model_dump(mode="json"),
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
    )


async def _invalid_username_length_error_handler(
    _request: Request, exc: Exception
) -> JSONResponse:
    """Обработать исключение InvalidUsernameLengthError.

    Возвращает клиенту ответ с HTTP 422 Unprocessable Content, если
    длина имени пользователя выходит за допустимые пределы.

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
        Ответ с ошибкой 422.
    """
    return JSONResponse(
        content=StandardResponse(
            code=APICode.VALIDATION_ERROR, detail=str(exc)
        ).model_dump(mode="json"),
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
    )


async def _invalid_username_format_error_handler(
    _request: Request, exc: Exception
) -> JSONResponse:
    """Обработать исключение InvalidUsernameFormatError.

    Возвращает клиенту ответ с HTTP 422 Unprocessable Content, если
    имя пользователя содержит недопустимые символы или не соответствует
    разрешённому паттерну.

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
        Ответ с ошибкой 422.
    """
    return JSONResponse(
        content=StandardResponse(
            code=APICode.VALIDATION_ERROR, detail=str(exc)
        ).model_dump(mode="json"),
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
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
        InvalidAvatarUrlLengthError, _invalid_avatar_url_length_error_handler
    )
    app.add_exception_handler(InvalidAvatarUrlError, _invalid_avatar_url_error_handler)
    app.add_exception_handler(
        InvalidDisplayNameLengthError, _invalid_display_name_length_error_handler
    )
    app.add_exception_handler(
        InvalidPasswordLengthError, _invalid_password_length_error_handler
    )
    app.add_exception_handler(
        InvalidUsernameLengthError, _invalid_username_length_error_handler
    )
    app.add_exception_handler(
        InvalidUsernameFormatError, _invalid_username_format_error_handler
    )
