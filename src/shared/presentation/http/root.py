from fastapi import APIRouter, status

from src.shared.presentation.http import APICode
from src.shared.presentation.http.schemas.standard import StandardResponse

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


@api_root_router.get(
    "/coffee",
    response_model=StandardResponse,
    status_code=status.HTTP_418_IM_A_TEAPOT,
    include_in_schema=False,
)
async def coffee() -> StandardResponse:
    """Пасхальное яйцо, возвращающее знаменитый ответ "Я - заварочный чайник".

    Эта конечная точка реализует шутливый стандарт *RFC 2324*. Она возвращает
    ошибку с кодом состояния **418 I'm a teapot**, указывая на то, что данный
    ресурс является чайником и не может выполнять функции кофеварки.

    Returns
    -------
    StandardResponse
        Объект ответа с кодом ошибки ``APICode.I_AM_A_TEAPOT`` и сообщением
        'I cannot brew coffee, I am a teapot.'.
    """
    return StandardResponse(
        code=APICode.I_AM_A_TEAPOT, detail="I cannot brew coffee, I am a teapot."
    )
