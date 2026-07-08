from fastapi import APIRouter, status

from src.presentation.http.schemas.standard import StandardResponse

api_root_router = APIRouter(tags=["root"])


@api_root_router.get(
    "/health",
    response_model=StandardResponse,
    status_code=status.HTTP_200_OK,
    summary="Проверка работоспособности API.",
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
