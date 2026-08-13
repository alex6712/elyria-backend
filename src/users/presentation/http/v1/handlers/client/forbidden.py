from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from src.shared.presentation.http import APICode
from src.shared.presentation.http.schemas import StandardResponse
from src.users.domain.exceptions import InactiveUserError


async def _inactive_user_error_handler(
    _request: Request, exc: Exception
) -> JSONResponse:
    """Обработать исключение InactiveUserError.

    Возвращает клиенту ответ с HTTP 403 Forbidden, если выполняется
    операция, требующая активной учётной записи, для неактивного
    пользователя (вход или обновление сессии).

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
        Ответ с ошибкой 403.
    """
    return JSONResponse(
        content=StandardResponse(
            code=APICode.INACTIVE_USER, detail=str(exc)
        ).model_dump(mode="json"),
        status_code=status.HTTP_403_FORBIDDEN,
    )


def register(app: FastAPI) -> None:
    """Зарегистрировать обработчик исключений на приложении.

    Parameters
    ----------
    app : FastAPI
        Экземпляр FastAPI-приложения, на который регистрируется
        обработчик.
    """
    app.add_exception_handler(InactiveUserError, _inactive_user_error_handler)
