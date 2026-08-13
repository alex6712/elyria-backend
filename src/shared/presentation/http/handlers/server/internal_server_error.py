from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from src.shared.application.exceptions import UnitOfWorkNotEnteredError
from src.shared.presentation.http import APICode
from src.shared.presentation.http.schemas import StandardResponse


async def _internal_server_error_handler(
    _request: Request, _exc: Exception
) -> JSONResponse:
    """Обработать непредвиденную ошибку сервера.

    Универсальный обработчик для ошибок, которые не должны
    возникать при нормальной работе (в том числе
    ``UnitOfWorkNotEnteredError``). Возвращает ответ с кодом 500
    и фиксированным сообщением, не раскрывая внутренние детали
    ошибки клиенту.

    Parameters
    ----------
    _request : Request
        Объект запроса FastAPI, содержащий информацию о входящем
        HTTP-запросе (не используется).
    _exc : Exception
        Необработанное исключение (не используется при формировании
        ответа).

    Returns
    -------
    JSONResponse
        Ответ с ошибкой 500.
    """
    return JSONResponse(
        content=StandardResponse(
            code=APICode.INTERNAL_SERVER_ERROR, detail="Internal server error."
        ).model_dump(mode="json"),
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


def register(app: FastAPI) -> None:
    """Зарегистрировать обработчики исключений на приложении.

    Регистрирует обработчик для ``UnitOfWorkNotEnteredError``
    и универсальный обработчик непредвиденных ошибок.

    Parameters
    ----------
    app : FastAPI
        Экземпляр FastAPI-приложения, на который регистрируются
        обработчики.
    """
    app.add_exception_handler(UnitOfWorkNotEnteredError, _internal_server_error_handler)
    app.add_exception_handler(Exception, _internal_server_error_handler)
