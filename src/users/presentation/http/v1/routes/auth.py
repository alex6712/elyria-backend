import textwrap
from typing import Annotated

from fastapi import APIRouter, Body, Request, status

from src.shared.presentation.http.schemas import StandardResponse
from src.users.application.commands import RegisterUserCommand
from src.users.domain.value_objects import DisplayName, Password, Username
from src.users.presentation.http.v1.schemas import RegisterUserRequest

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=StandardResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Регистрация пользователя.",
    description=textwrap.dedent("""\
        Создаёт новую учётную запись пользователя в системе.

        Для регистрации требуется передать следующие данные:
        - ``username``: уникальное имя пользователя;
        - ``password``: пароль пользователя (должен соответствовать требованиям политики
        безопасности);
        - ``displayName``: отображаемое имя, которое будет видно другим пользователям.

        При успешной регистрации система создаёт учётную запись, инициализирует
        необходимые ресурсы и возвращает ответ со статусом ``201 Created``.
        В случае ошибки (например, при занятом ``username`` или несоответствии пароля
        требованиям) возвращается соответствующий HTTP-код и сообщение об ошибке.
    """),
    response_description="Успешная регистрация",
)
async def register(
    request: Request,
    body: Annotated[
        RegisterUserRequest,
        Body(description="Схема запроса на регистрацию пользователя."),
    ],
) -> StandardResponse:
    """Регистрация нового пользователя.

    Принимает данные для регистрации (имя пользователя, пароль, отображаемое имя),
    создает нового пользователя в системе.

    Parameters
    ----------
    request : Request
        Объект HTTP-запроса FastAPI. Используется для доступа к глобальному
        DI-контейнеру через атрибуты состояния приложения.
    body : RegisterUserRequest
        Валидированная схема тела запроса, содержащая данные для регистрации:
        username (str), password (str) и display_name (str).

    Returns
    -------
    StandardResponse
        Ответ с кодом 201 и сообщением об успешной регистрации.
    """
    await request.app.state.container.users.register_user().execute(
        RegisterUserCommand(
            username=Username(body.username),
            password=Password(body.password),
            display_name=DisplayName(body.display_name),
        )
    )

    return StandardResponse(detail="User registered successfully.")
