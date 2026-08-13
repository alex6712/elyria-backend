from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from src.shared.presentation.http import APICode
from src.shared.presentation.http.schemas import StandardResponse
from src.users.application.exceptions import CompromisedPasswordError


async def _compromised_password_error_handler(
    _request: Request, exc: Exception
) -> JSONResponse:
    """Обработать исключение CompromisedPasswordError.

    Возвращает клиенту ответ с HTTP 400 Bad Request в случае,
    если переданный при регистрации пароль встречается в известных
    утечках данных. Клиенту не раскрываются детали проверки.

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
        Ответ с ошибкой 400.
    """
    return JSONResponse(
        content=StandardResponse(
            code=APICode.COMPROMISED_PASSWORD, detail=str(exc)
        ).model_dump(mode="json"),
        status_code=status.HTTP_400_BAD_REQUEST,
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
        CompromisedPasswordError, _compromised_password_error_handler
    )
