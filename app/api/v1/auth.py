from typing import Annotated

from fastapi import APIRouter, Body, Request, Response, status

from app.core.cookies import delete_auth_cookies, set_auth_cookies
from app.core.dependencies.auth import (
    SignInCredentialsDependency,
    StrictAuthenticationDependency,
)
from app.core.dependencies.services import ServiceManagerDependency
from app.core.dependencies.settings import SettingsDependency
from app.core.docs import (
    AUTHORIZATION_ERROR_REF,
    CHANGE_PASSWORD_ERROR_REF,
    CHANGE_PASSWORD_VALIDATION_ERROR_REF,
    LOGIN_ERROR_REF,
    RATE_LIMIT_ERROR_REF,
    REGISTER_ERROR_REF,
)
from app.core.rate_limiter import (
    CHANGE_PASSWORD_LIMIT,
    LOGIN_LIMIT,
    REGISTER_LIMIT,
    limiter,
)
from app.schemas.v1.requests.auth import ChangePasswordRequest, RegisterRequest
from app.schemas.v1.responses.auth import LoggedInUserDTO, LoginResponse
from app.schemas.v1.responses.standard import StandardResponse

router = APIRouter(prefix="/auth", tags=["authorization"])


@router.post(
    "/register",
    response_model=StandardResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Регистрация пользователя.",
    response_description="Успешная регистрация",
    responses={422: REGISTER_ERROR_REF, 429: RATE_LIMIT_ERROR_REF},
)
@limiter.limit(REGISTER_LIMIT)  # type: ignore
async def register(
    request: Request,
    response: Response,
    body: Annotated[
        RegisterRequest, Body(description="Схема запроса на регистрацию пользователя.")
    ],
    services: ServiceManagerDependency,
) -> StandardResponse:
    """Регистрация нового пользователя.

    Принимает данные для регистрации (имя пользователя и пароль),
    создает нового пользователя в системе.

    Parameters
    ----------
    request : Request
        Объект HTTP-запроса. Требуется для работы slowapi.Limiter
        при определении rate limit по IP-адресу клиента.
    response : Response
        Объект HTTP-ответа. Требуется для работы slowapi.Limiter
        при инъекции заголовков X-RateLimit-*.
    body : RegisterRequest
        Данные, полученные от клиента в теле запроса.
    services : ServiceManager
        Менеджер сервисов уровня запроса (request-scoped).

        Предоставляет доступ к бизнес-сервисам приложения
        (например, auth, user, note, file и др.) через единый
        контейнер зависимостей.

    Returns
    -------
    StandardResponse
        Ответ с кодом 201 и сообщением об успешной регистрации.
    """
    await services.auth.register(body.username, body.password)

    return StandardResponse(detail="User created successfully.")


@router.post(
    "/login",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
    summary="Аутентификация пользователя.",
    response_description="Успешная аутентификация",
    responses={401: LOGIN_ERROR_REF, 429: RATE_LIMIT_ERROR_REF},
)
@limiter.limit(LOGIN_LIMIT)  # type: ignore
async def login(
    request: Request,
    response: Response,
    form_data: SignInCredentialsDependency,
    services: ServiceManagerDependency,
    settings: SettingsDependency,
) -> LoginResponse:
    """Аутентификация пользователя.

    Принимает учётные данные пользователя, проверяет их и
    устанавливает HttpOnly-cookie с парой JWT-токенов.

    В cookie передаются:

    - `ACCESS_TOKEN_COOKIE_NAME` (по умолчанию `ml_at`) -
      короткоживущий access-токен, используемый при
      авторизации защищённых эндпоинтов;
    - `REFRESH_TOKEN_COOKIE_NAME` (по умолчанию `ml_rt`) -
      долгоживущий refresh-токен, используемый
      auth-зависимостью `_resolve_auth` для прозрачной
      ротации пары токенов при истечении access-токена.

    Тело ответа намеренно не содержит JWT - фронтенд
    получает только публичную информацию о пользователе
    для инициализации клиентского состояния.

    Parameters
    ----------
    request : Request
        Объект HTTP-запроса. Требуется для работы slowapi.Limiter
        при определении rate limit по IP-адресу клиента.
    response : Response
        Объект HTTP-ответа, в который будут добавлены
        `Set-Cookie` заголовки. Также используется
        slowapi.Limiter для инъекции заголовков
        `X-RateLimit-*`.
    form_data : SignInCredentialsDependency
        Зависимость для получения учётных данных из формы
        (поля `username` и `password`).
    services : ServiceManager
        Менеджер сервисов уровня запроса (request-scoped).

        Предоставляет доступ к бизнес-сервисам приложения
        (например, auth, user, note, file и др.) через единый
        контейнер зависимостей.
    settings : Settings
        Конфигурация приложения, описывающая имена и
        атрибуты auth-cookie.

    Returns
    -------
    LoginResponse
        Ответ с публичными данными вошедшего пользователя.
    """
    result = await services.auth.login(form_data.username, form_data.password)

    set_auth_cookies(
        response,
        access_token=result.tokens.access,
        refresh_token=result.tokens.refresh,
        settings=settings,
    )

    return LoginResponse(
        detail="Login successful.",
        user=LoggedInUserDTO(id=str(result.user_id), username=result.username),
    )


@router.post(
    "/logout",
    response_model=StandardResponse,
    status_code=status.HTTP_200_OK,
    summary="Выход из системы.",
    response_description="Успешный выход из системы",
    responses={401: AUTHORIZATION_ERROR_REF},
)
async def logout(
    response: Response,
    services: ServiceManagerDependency,
    settings: SettingsDependency,
    payload: StrictAuthenticationDependency,
) -> StandardResponse:
    """Завершение текущей сессии пользователя.

    Выполняет:

    - добавление `jti` access-токена в Redis blacklist
      с TTL до окончания срока его действия;
    - удаление связанной пользовательской сессии
      (refresh-токен автоматически становится невалидным);
    - очистку auth-cookie на стороне клиента
      через `Set-Cookie` с `Max-Age=0`.

    Для выполнения операции требуется валидный access-cookie.
    После выполнения запроса все auth-cookie пользователя
    становятся недействительными.

    Parameters
    ----------
    response : Response
        Объект HTTP-ответа, в который будут добавлены
        `Set-Cookie` заголовки для очистки cookie.
    services : ServiceManager
        Менеджер сервисов уровня запроса (request-scoped).

        Предоставляет доступ к бизнес-сервисам приложения
        (например, auth, user, note, file и др.) через единый
        контейнер зависимостей.
    settings : Settings
        Конфигурация приложения, описывающая имена и
        атрибуты auth-cookie.
    payload : AccessTokenPayload
        Полезная нагрузка (payload) access-токена,
        возвращаемая `StrictAuthenticationDependency`
        после разрешения сессии через auth-зависимость
        `_resolve_auth` (с валидацией access-cookie
        или прозрачной ротацией по refresh-cookie).

    Returns
    -------
    StandardResponse
        Стандартный ответ с сообщением об успешном выходе
        из системы.

    Notes
    -----
    - Access-токен должен быть валидным на момент
      выполнения запроса.
    - После выполнения запроса auth-cookie пользователя
      становятся недействительными.
    """
    await services.auth.logout(payload)

    delete_auth_cookies(response, settings=settings)

    return StandardResponse(detail="User successfully logout.")


@router.post(
    "/change-password",
    response_model=StandardResponse,
    status_code=status.HTTP_200_OK,
    summary="Смена пароля пользователя.",
    response_description="Пароль пользователя изменён успешно",
    responses={
        400: CHANGE_PASSWORD_ERROR_REF,
        401: AUTHORIZATION_ERROR_REF,
        422: CHANGE_PASSWORD_VALIDATION_ERROR_REF,
        429: RATE_LIMIT_ERROR_REF,
    },
)
@limiter.limit(CHANGE_PASSWORD_LIMIT)  # type: ignore
async def change_password(
    request: Request,
    response: Response,
    body: Annotated[
        ChangePasswordRequest,
        Body(description="Схема запроса на изменение пароля пользователя."),
    ],
    services: ServiceManagerDependency,
    payload: StrictAuthenticationDependency,
) -> StandardResponse:
    """Смена пароля текущего пользователя.

    Валидирует текущий пароль и заменяет его на новый.
    Требует наличия действующего access-токена в auth-cookie.

    Parameters
    ----------
    request : Request
        Объект HTTP-запроса. Требуется для работы slowapi.Limiter
        при определении rate limit по IP-адресу клиента.
    response : Response
        Объект HTTP-ответа. Требуется для работы slowapi.Limiter
        при инъекции заголовков X-RateLimit-*.
    body : ChangePasswordRequest
        Тело запроса, содержащее текущий и новый пароли пользователя.
    services : ServiceManager
        Менеджер сервисов уровня запроса (request-scoped).

        Предоставляет доступ к бизнес-сервисам приложения
        (например, auth, user, note, file и др.) через единый
        контейнер зависимостей.
    payload : AccessTokenPayload
        Полезная нагрузка (payload) токена доступа.
        Получена автоматически из зависимости на строгую аутентификацию.

    Returns
    -------
    StandardResponse
        Стандартный ответ с подтверждением успешной смены пароля.
    """
    await services.auth.change_password(
        body.current_password, body.new_password, payload
    )

    return StandardResponse(detail="User's password successfully changed.")
