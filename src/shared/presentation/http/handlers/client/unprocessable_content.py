from typing import cast

from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from src.shared.presentation.http.schemas import ValidationErrorResponse


async def _request_validation_error_handler(
    _request: Request, exc: Exception
) -> JSONResponse:
    """Обработать ошибку валидации запроса RequestValidationError.

    Заменяет стандартный ответ FastAPI на стандартизированный
    ответ с кодом ``VALIDATION_ERROR`` и списком ошибок валидации,
    сохраняя единый формат ответов API.

    Parameters
    ----------
    _request : Request
        Объект запроса FastAPI, содержащий информацию о входящем
        HTTP-запросе (не используется).
    exc : Exception
        Исключение, содержащее список ошибок валидации переданных
        данных (представлен общий тип для соответствия ожидаемой сигнатуре, сужается
        в теле до RequestValidationError).

    Returns
    -------
    JSONResponse
        Ответ с ошибкой 422.
    """
    narrowed = cast(RequestValidationError, exc)

    return JSONResponse(
        content=ValidationErrorResponse(
            detail=jsonable_encoder(narrowed.errors())
        ).model_dump(mode="json"),
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
    )


def register(app: FastAPI) -> None:
    """Зарегистрировать обработчик исключений на приложении.

    Parameters
    ----------
    app : FastAPI
        Экземпляр FastAPI-приложения, на который регистрируется
        обработчик.
    """
    app.add_exception_handler(RequestValidationError, _request_validation_error_handler)
