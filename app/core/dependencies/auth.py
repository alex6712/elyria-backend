from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from app.config import get_settings
from app.core.dependencies.services import ServiceManagerDependency
from app.core.dependencies.settings import SettingsDependency
from app.core.exceptions.auth import (
    InvalidTokenException,
    TokenNotPassedException,
    TokenRevokedException,
    TokenSignatureExpiredException,
)
from app.schemas.dto.payload import AccessTokenPayload

settings = get_settings()

SignInCredentialsDependency = Annotated[OAuth2PasswordRequestForm, Depends()]
"""Зависимость на получение реквизитов для входа в систему.

Принимает данные из тела запроса в формате
`application/x-www-form-urlencoded` согласно спецификации
OAuth2 Password Grant (поля `username` и `password`).
"""

_oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"/{settings.CURRENT_API_PATH}/auth/login",
    auto_error=False,
    refreshUrl=f"/{settings.CURRENT_API_PATH}/auth/refresh",
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


async def _resolve_auth(
    services: ServiceManagerDependency, access_token: ExtractAccessTokenDependency
) -> AccessTokenPayload | None:
    """Разрешает сессию пользователя по access-токену.

    Извлекает access-токен из заголовка `Authorization: Bearer`
    и проверяет его валидность (корректная подпись + отсутствие
    в Redis blacklist). При успехе возвращает payload токена.

    Если токен отсутствует или истёк/отозван - возвращает `None`.
    Прозрачная ротация по refresh-токену не выполняется.

    Parameters
    ----------
    services : ServiceManager
        Request-scoped менеджер сервисов, предоставляющий
        доступ к `AuthService` для валидации access-токена.
        Использует общий с маршрутом `UnitOfWork`.
    access_token : str | None
        Токен доступа, извлечённые из Authorization заголовка
        запроса.

    Returns
    -------
    AccessTokenPayload | None
        Валидированный payload access-токена при его наличии
        либо `None`, если токен отсутствует, истёк или отозван.
    """
    if access_token is None:
        return None

    try:
        return await services.auth.validate_access_token(access_token)
    except (
        TokenSignatureExpiredException,
        TokenRevokedException,
        InvalidTokenException,
    ):
        pass


SoftAuthenticationDependency = Annotated[
    AccessTokenPayload | None, Depends(_resolve_auth)
]
"""Зависимость для мягкой проверки аутентификации.

Используется в эндпоинтах, доступных как аутентифицированным,
так и неаутентифицированным пользователям.

При отсутствии валидной сессии возвращает `None` -
endpoint сам решает, что с этим делать.
"""


async def _require_auth(payload: SoftAuthenticationDependency) -> AccessTokenPayload:
    """Приводит мягкий результат `_resolve_auth` к строгой форме.

    Используется как обёртка над `SoftAuthenticationDependency`
    для формирования `StrictAuthenticationDependency`.

    Parameters
    ----------
    payload : AccessTokenPayload | None
        Результат `_resolve_auth`. Может быть `None`, если
        валидная сессия не была сформирована ни по access,
        ни по refresh cookie.

    Returns
    -------
    AccessTokenPayload
        Гарантированно непустой payload access-токена.

    Raises
    ------
    TokenNotPassedException
        Если `payload is None` - пользователь не аутентифицирован.
        Приводит к HTTP 401 через зарегистрированный
        exception handler.
    """
    if payload is None:
        raise TokenNotPassedException(
            detail=(
                "Access token is missing. Provide it in the Authorization: Bearer <token> header."
            ),
            token_type="access",
        )

    return payload


StrictAuthenticationDependency = Annotated[AccessTokenPayload, Depends(_require_auth)]
"""Зависимость для строгой проверки аутентификации.

Используется в защищённых эндпоинтах, требующих
обязательной аутентификации. При отсутствии валидного
access-токена в заголовке Authorization поднимает
`TokenNotPassedException` (HTTP 401).
"""
