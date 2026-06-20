from typing import Annotated, Any, Callable, Coroutine

from fastapi import Depends, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from app.config import get_settings
from app.core.dependencies.services import ServiceManagerDependency
from app.core.dependencies.settings import SettingsDependency
from app.core.exceptions.auth import AuthDomainException
from app.schemas.dto.payload import AccessTokenPayload

_settings = get_settings()

SignInCredentialsDependency = Annotated[OAuth2PasswordRequestForm, Depends()]
"""Зависимость на получение реквизитов для входа в систему.

Принимает данные из тела запроса в формате
`application/x-www-form-urlencoded` согласно спецификации
OAuth2 Password Grant (поля `username` и `password`).
"""

_oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"/{_settings.CURRENT_API_PATH}/auth/login",
    auto_error=False,
    refreshUrl=f"/{_settings.CURRENT_API_PATH}/auth/refresh",
)

ExtractAccessTokenDependency = Annotated[str | None, Depends(_oauth2_scheme)]
"""Зависимость на получение токена доступа из заголовков запроса."""


def _get_refresh_token(request: Request, settings: SettingsDependency) -> str | None:
    """Извлекает refresh-токен из cookie запроса.

    Parameters
    ----------
    request : Request
        Объект входящего HTTP-запроса.
    settings : Settings
        Конфигурация приложения, описывающая имя cookie
        для refresh-токена.

    Returns
    -------
    str | None
        Значение refresh-токена либо `None`, если cookie
        отсутствует.
    """
    return request.cookies.get(settings.REFRESH_TOKEN_COOKIE_NAME)


ExtractRefreshTokenDependency = Annotated[str | None, Depends(_get_refresh_token)]
"""Зависимость на получение токена обновления из HttpOnly Cookie."""

_AuthDependencyCallable = Callable[
    [ExtractAccessTokenDependency, ServiceManagerDependency],
    Coroutine[Any, Any, AccessTokenPayload | None],
]
"""Тип вызываемого объекта зависимости аутентификации."""


def _check_auth(strict: bool) -> _AuthDependencyCallable:
    """Фабрика для создания зависимостей аутентификации.

    Генерирует зависимости FastAPI с гибким поведением при ошибках
    аутентификации. Позволяет выбирать между строгим и мягким режимом
    проверки access token.

    Parameters
    ----------
    strict : bool
        Режим обработки ошибок:
        - True: строгий режим - исключение пробрасывается.
        - False: мягкий режим - при ошибке возвращается None.

    Returns
    -------
    _AuthDependencyCallable
        Функция зависимости, использующая ServiceManager
        для доступа к AuthService.

    See Also
    --------
    SoftAuthenticationDependency
    StrictAuthenticationDependency
    """

    async def dependency(
        access_token: ExtractAccessTokenDependency, services: ServiceManagerDependency
    ) -> AccessTokenPayload | None:
        """Внутренняя функция зависимости, выполняющая проверку токена.

        Parameters
        ----------
        access_token : str | None
            JWT access token, извлечённый из заголовков запроса.
        services : ServiceManagerDependency
            Менеджер сервисов уровня запроса.

        Returns
        -------
        AccessTokenPayload | None
            Расшифрованные данные токена при успешной проверке.
            В мягком режиме при ошибке возвращается None.

        Raises
        ------
        AuthDomainException
            В строгом режиме при ошибке аутентификации.

        Notes
        -----
        Поведение:
        1. В строгом режиме доменные исключения пробрасываются.
        2. В мягком режиме AuthDomainException преобразуется в None.
        3. Недоменные исключения никогда не подавляются.
        """
        try:
            return await services.auth.validate_access_token(access_token)
        except AuthDomainException as e:
            if strict:
                raise e
            return None

    return dependency


SoftAuthenticationDependency = Annotated[
    AccessTokenPayload | None, Depends(_check_auth(strict=False))
]
"""Зависимость для мягкой проверки аутентификации.

Используется в эндпоинтах, доступных как аутентифицированным,
так и неаутентифицированным пользователям.
"""

StrictAuthenticationDependency = Annotated[
    AccessTokenPayload, Depends(_check_auth(strict=True))
]
"""Зависимость для строгой проверки аутентификации.

Используется в защищённых эндпоинтах,
требующих обязательной аутентификации.
"""
