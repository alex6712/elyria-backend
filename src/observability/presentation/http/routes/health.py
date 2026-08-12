import textwrap

from fastapi import APIRouter, status

from src.shared.presentation.http.schemas import StandardResponse

router = APIRouter(prefix="/health", tags=["root"])


@router.get(
    "",
    response_model=StandardResponse,
    status_code=status.HTTP_200_OK,
    summary="Проверка работоспособности API.",
    description=textwrap.dedent("""\
        Проверяет текущее состояние API и готовность сервиса к обработке запросов.

        Этот эндпоинт не выполняет бизнес‑логику и не зависит от внешних зависимостей,
        он лишь подтверждает, что приложение запущено и способно отвечать на запросы.
    """),
    response_description="API работает",
)
async def health() -> StandardResponse:
    """Путь для проверки работоспособности API.

    Ничего не делает, кроме как возвращает положительный ответ на запрос.

    Returns
    -------
    StandardResponse
        Ответ о корректной работе сервера.
    """
    return StandardResponse(detail="API works!")
