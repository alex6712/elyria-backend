import textwrap
from typing import Annotated

from fastapi import APIRouter, Body, Response, status

from src.users.application.commands import RegisterUserCommand
from src.users.domain.value_objects import DisplayName, Password, Username
from src.users.presentation.http.dependencies import (
    AuthCookiesProviderDependency,
    RegisterUserDependency,
)
from src.users.presentation.http.v1.schemas import (
    RegisterUserRequest,
    RegisterUserResponse,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=RegisterUserResponse,
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
    response: Response,
    body: Annotated[
        RegisterUserRequest,
        Body(description="Схема запроса на регистрацию пользователя."),
    ],
    register_user: RegisterUserDependency,
    auth_cookies_provider: AuthCookiesProviderDependency,
) -> RegisterUserResponse:
    """Регистрация нового пользователя.

    Принимает данные для регистрации (имя пользователя, пароль, отображаемое имя),
    создает нового пользователя в системе.

    Parameters
    ----------
    response : Response
        Объект HTTP-ответа FastAPI. Используется для установки
        HttpOnly-cookie с refresh-токеном.
    body : RegisterUserRequest
        Валидированная схема тела запроса, содержащая данные для регистрации:
        username (str), password (str) и display_name (str).
    register_user : RegisterUserUseCase
        Use Case регистрации пользователя, полученный через DI-зависимость
        FastAPI из контейнера приложения.
    auth_cookies_provider : AuthCookiesProvider
        Провайдер auth-cookie, полученный через DI-зависимость FastAPI
        из контейнера приложения. Используется для установки HttpOnly-cookie
        с refresh-токеном в ответ.

    Returns
    -------
    RegisterUserResponse
        Ответ с кодом 201, идентификатором созданного пользователя
        и access-токеном для немедленной аутентификации. Refresh-токен
        устанавливается отдельно в HttpOnly-cookie.
    """
    result = await register_user.execute(
        RegisterUserCommand(
            username=Username(body.username),
            password=Password(body.password),
            display_name=DisplayName(body.display_name),
        )
    )

    auth_cookies_provider.set_refresh_token_cookie(
        response=response, refresh_token=result.refresh_token
    )

    return RegisterUserResponse(
        detail="User registered successfully.",
        user_id=result.user_id,
        access_token=result.access_token,
    )
