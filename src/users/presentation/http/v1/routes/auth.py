import textwrap
from typing import Annotated

from fastapi import APIRouter, Body, Request, Response, status

from src.shared.presentation.http.schemas import StandardResponse
from src.users.application.commands import (
    LoginCommand,
    LogoutCommand,
    RefreshSessionCommand,
    RegisterUserCommand,
)
from src.users.domain.value_objects import DisplayName, Password, Username
from src.users.presentation.http.dependencies import (
    AccessTokenDependency,
    AuthCookiesProviderDependency,
    LoginUserDependency,
    LogoutDependency,
    RefreshSessionDependency,
    RegisterUserDependency,
)
from src.users.presentation.http.exceptions import (
    AccessTokenMissingError,
    RefreshTokenMissingError,
)
from src.users.presentation.http.v1.schemas import (
    LoginRequest,
    LoginResponse,
    RefreshSessionResponse,
    RegisterUserRequest,
    RegisterUserResponse,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/login",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
    summary="Вход в систему.",
    description=textwrap.dedent("""\
        Аутентифицирует пользователя по имени пользователя и паролю.

        Для входа требуется передать следующие данные:
        - ``username``: имя пользователя (логин);
        - ``password``: пароль пользователя.

        При успешной аутентификации система создаёт новую сессию,
        возвращает access-токен в теле ответа и устанавливает
        HttpOnly-cookie с refresh-токеном.

        В случае ошибки (неверные учётные данные, неактивная учётная
        запись или несоответствие данных требованиям) возвращается
        соответствующий HTTP-код и сообщение об ошибке.
    """),
    response_description="Успешная аутентификация",
)
async def login(
    response: Response,
    body: Annotated[LoginRequest, Body(description="Схема запроса на вход в систему.")],
    login_use_case: LoginUserDependency,
    auth_cookies_provider: AuthCookiesProviderDependency,
) -> LoginResponse:
    """Вход пользователя в систему.

    Принимает учётные данные (имя пользователя и пароль), аутентифицирует
    пользователя и создаёт новую пользовательскую сессию.

    Parameters
    ----------
    response : Response
        Объект HTTP-ответа FastAPI. Используется для установки
        HttpOnly-cookie с refresh-токеном.
    body : LoginRequest
        Валидированная схема тела запроса, содержащая данные для входа:
        username (str) и password (str).
    login_use_case : LoginUseCase
        Use Case аутентификации пользователя, полученный через DI-зависимость
        FastAPI из контейнера приложения.
    auth_cookies_provider : AuthCookiesProvider
        Провайдер auth-cookie, полученный через DI-зависимость FastAPI
        из контейнера приложения. Используется для установки HttpOnly-cookie
        с refresh-токеном в ответ.

    Returns
    -------
    LoginResponse
        Ответ с кодом 200 и access-токеном для дальнейшей аутентификации
        запросов. Refresh-токен устанавливается отдельно в HttpOnly-cookie.
    """
    result = await login_use_case.execute(
        LoginCommand(username=Username(body.username), password=Password(body.password))
    )

    auth_cookies_provider.set_refresh_token_cookie(
        response=response, refresh_token=result.refresh_token
    )

    return LoginResponse(
        detail="User logged in successfully.", access_token=result.access_token
    )


@router.post(
    "/logout",
    response_model=StandardResponse,
    status_code=status.HTTP_200_OK,
    summary="Завершение сессии пользователя.",
    description=textwrap.dedent("""\
        Завершает пользовательскую сессию и отзывает токены.

        Access-токен передаётся в заголовке ``Authorization``
        в формате ``Bearer <token>``. При успешном завершении сессии
        access-токен добавляется в чёрный список, связанная сессия
        помечается как отозванная, а HttpOnly-cookie с refresh-токеном
        удаляется из ответа.

        Операция идемпотентна: повторный вызов с отозванным токеном
        не является ошибкой.

        В случае ошибки (отсутствие access-токена, истёкший токен
        или недействительная подпись) возвращается соответствующий
        HTTP-код и сообщение об ошибке.
    """),
    response_description="Успешное завершение сессии",
)
async def logout(
    response: Response,
    credentials: AccessTokenDependency,
    logout_user: LogoutDependency,
    auth_cookies_provider: AuthCookiesProviderDependency,
) -> StandardResponse:
    """Завершение пользовательской сессии.

    Принимает access-токен из Bearer-заголовка, отзывает его
    и связанную с ним сессию, удаляет HttpOnly-cookie с refresh-токеном.

    Parameters
    ----------
    response : Response
        Объект HTTP-ответа FastAPI. Используется для удаления
        HttpOnly-cookie с refresh-токеном.
    credentials : HTTPAuthorizationCredentials | None
        Учётные данные Bearer-схемы из заголовка ``Authorization``
        входящего запроса. Значение ``None`` означает отсутствие
        заголовка либо некорректную схему.
    logout_user : LogoutUseCase
        Use Case завершения сессии, полученный через DI-зависимость
        FastAPI из контейнера приложения.
    auth_cookies_provider : AuthCookiesProvider
        Провайдер auth-cookie, полученный через DI-зависимость FastAPI
        из контейнера приложения. Используется для удаления HttpOnly-cookie
        с refresh-токеном из ответа.

    Returns
    -------
    StandardResponse
        Ответ с кодом 200 и сообщением об успешном завершении сессии.

    Raises
    ------
    AccessTokenMissingError
        Если заголовок ``Authorization`` с Bearer-схемой отсутствует
        во входящем запросе либо имеет некорректный формат.
    """
    if credentials is None:
        raise AccessTokenMissingError(
            "Access token is missing. "
            + "Provide it in the Authorization: Bearer <token> header."
        )

    await logout_user.execute(LogoutCommand(access_token=credentials.credentials))

    auth_cookies_provider.delete_refresh_token_cookie(response)

    return StandardResponse(detail="User logged out successfully.")


@router.post(
    "/refresh",
    response_model=RefreshSessionResponse,
    status_code=status.HTTP_200_OK,
    summary="Обновление пары токенов.",
    description=textwrap.dedent("""\
        Обновляет access и refresh токены по действующему refresh-токену.

        Refresh-токен передаётся не в теле запроса, а в HttpOnly-cookie,
        установленной при входе в систему или при предыдущем обновлении
        пары токенов.

        При успешном обновлении система ротирует сессию: предыдущий
        refresh-токен аннулируется, новый refresh-токен устанавливается
        в HttpOnly-cookie, а access-токен возвращается в теле ответа.

        В случае ошибки (отсутствие или недействительность refresh-токена,
        неактивная учётная запись, отсутствие или отзыв сессии) возвращается
        соответствующий HTTP-код и сообщение об ошибке.
    """),
    response_description="Успешное обновление пары токенов",
)
async def refresh(
    request: Request,
    response: Response,
    refresh_session: RefreshSessionDependency,
    auth_cookies_provider: AuthCookiesProviderDependency,
) -> RefreshSessionResponse:
    """Обновление пары access/refresh токенов.

    Извлекает refresh-токен из HttpOnly-cookie входящего запроса,
    валидирует его и связанную с ним сессию, ротирует сессию
    и выпускает новую пару токенов.

    Parameters
    ----------
    request : Request
        Объект входящего HTTP-запроса FastAPI. Используется для чтения
        HttpOnly-cookie с refresh-токеном.
    response : Response
        Объект HTTP-ответа FastAPI. Используется для установки
        HttpOnly-cookie с новым refresh-токеном.
    refresh_session : RefreshSessionUseCase
        Use Case обновления пары токенов, полученный через DI-зависимость
        FastAPI из контейнера приложения.
    auth_cookies_provider : AuthCookiesProvider
        Провайдер auth-cookie, полученный через DI-зависимость FastAPI
        из контейнера приложения. Используется для чтения refresh-токена
        из cookie запроса и установки HttpOnly-cookie с новым refresh-токеном
        в ответ.

    Returns
    -------
    RefreshSessionResponse
        Ответ с кодом 200 и новым access-токеном для дальнейшей
        аутентификации запросов. Новый refresh-токен устанавливается
        отдельно в HttpOnly-cookie.

    Raises
    ------
    RefreshTokenMissingError
        Если cookie с refresh-токеном отсутствует во входящем запросе.
    """
    refresh_token = auth_cookies_provider.get_refresh_token_cookie(request)

    if refresh_token is None:
        raise RefreshTokenMissingError(
            "Refresh token is missing. Provide it in the refresh token cookie."
        )

    result = await refresh_session.execute(
        RefreshSessionCommand(refresh_token=refresh_token)
    )

    auth_cookies_provider.set_refresh_token_cookie(
        response=response, refresh_token=result.refresh_token
    )

    return RefreshSessionResponse(
        detail="Session refreshed successfully.", access_token=result.access_token
    )


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
    register_user_use_case: RegisterUserDependency,
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
    register_user_use_case : RegisterUserUseCase
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
    result = await register_user_use_case.execute(
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
