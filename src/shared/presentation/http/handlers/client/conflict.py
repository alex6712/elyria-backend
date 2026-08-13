from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from src.shared.domain.exceptions import ConcurrentModificationError
from src.shared.presentation.http import APICode
from src.shared.presentation.http.schemas import StandardResponse


async def _concurrent_modification_error_handler(
    _request: Request, exc: Exception
) -> JSONResponse:
    """Обработать исключение ConcurrentModificationError.

    Возвращает клиенту ответ с HTTP 409 Conflict в случае, если
    версия агрегата в хранилище изменилась с момента его загрузки
    (конфликт оптимистичной блокировки). Клиент должен перезагрузить
    данные и повторить операцию осознанно.

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
            code=APICode.CONCURRENT_MODIFICATION, detail=str(exc)
        ).model_dump(mode="json"),
        status_code=status.HTTP_409_CONFLICT,
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
        ConcurrentModificationError, _concurrent_modification_error_handler
    )
