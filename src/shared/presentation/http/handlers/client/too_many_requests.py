from typing import cast

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from src.shared.application.exceptions import RateLimitExceededError
from src.shared.presentation.http import APICode
from src.shared.presentation.http.schemas import StandardResponse

X_RATE_LIMIT_LIMIT_HEADER = "X-Rate-Limit-Limit"
"""Заголовок с максимальным количеством запросов в окне."""

X_RATE_LIMIT_REMAINING_HEADER = "X-Rate-Limit-Remaining"
"""Заголовок с количеством запросов, доступных в текущем окне."""

RETRY_AFTER_HEADER = "Retry-After"
"""Заголовок с количеством секунд до сброса окна ограничения."""


async def _rate_limit_exceeded_error_handler(
    _request: Request, exc: Exception
) -> JSONResponse:
    """Обработать исключение RateLimitExceededError.

    Возвращает клиенту ответ с HTTP 429 Too Many Requests в случае,
    если исчерпан лимит количества запросов к операции. В ответе
    передаются заголовки ``X-Rate-Limit-Limit``,
    ``X-Rate-Limit-Remaining`` и ``Retry-After``, позволяющие
    клиенту определить величину лимита и время до возможности
    повторной попытки.

    Parameters
    ----------
    _request : Request
        Объект запроса FastAPI, содержащий информацию о входящем
        HTTP-запросе (не используется).
    exc : Exception
        Экземпляр исключения, из которого получаются значения
        счётчиков и текст сообщения об ошибке.

    Returns
    -------
    JSONResponse
        Ответ с ошибкой 429 и заголовками ограничения частоты.
    """
    narrowed = cast(RateLimitExceededError, exc)

    return JSONResponse(
        content=StandardResponse(
            code=APICode.RATE_LIMIT_EXCEEDED, detail=str(exc)
        ).model_dump(mode="json"),
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        headers={
            X_RATE_LIMIT_LIMIT_HEADER: str(narrowed.limit),
            X_RATE_LIMIT_REMAINING_HEADER: str(narrowed.remaining),
            RETRY_AFTER_HEADER: str(narrowed.retry_after),
        },
    )


def register(app: FastAPI) -> None:
    """Зарегистрировать обработчик исключений на приложении.

    Parameters
    ----------
    app : FastAPI
        Экземпляр FastAPI-приложения, на который регистрируется
        обработчик.
    """
    app.add_exception_handler(
        RateLimitExceededError, _rate_limit_exceeded_error_handler
    )
