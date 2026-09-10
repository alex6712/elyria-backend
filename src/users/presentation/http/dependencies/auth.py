from typing import Annotated

from fastapi import Depends, Request

from src.users.application.handlers.command import (
    ChangePasswordCommandHandler,
    LoginCommandHandler,
    LogoutCommandHandler,
    RefreshSessionCommandHandler,
    RegisterUserCommandHandler,
)
from src.users.presentation.http.services import AuthCookiesProvider


def _get_login_command_handler(request: Request) -> LoginCommandHandler:
    """Получить обработчик команды аутентификации из DI-контейнера.

    Доступ к нетипизированному ``request.app.state.container``
    выполняется напрямую - Starlette не поддерживает типизацию
    ``State`` нативно, поэтому возвращаемый тип принудительно
    объявляется сигнатурой функции.

    Parameters
    ----------
    request : Request
        Объект HTTP-запроса FastAPI. Используется для доступа
        к глобальному DI-контейнеру приложения через ``app.state``.

    Returns
    -------
    LoginCommandHandler
        Обработчик команды аутентификации пользователя.
    """
    return request.app.state.container.users.login_command_handler


LoginUserDependency = Annotated[
    LoginCommandHandler, Depends(_get_login_command_handler)
]
"""Типизированная FastAPI-зависимость обработчика команды аутентификации.

Инкапсулирует доступ к ``request.app.state.container`` и предоставляет
роутам готовый экземпляр :class:`LoginCommandHandler` без ручного
приведения типов. Используется как аннотация параметра обработчика:

```python
@router.post("/login")
async def login(
    login_user: LoginUserDependency,
    ...,
) -> LoginResponse:
    result = await login_user.execute(...)
```
"""


def _get_logout_command_handler(request: Request) -> LogoutCommandHandler:
    """Получить обработчик команды завершения сессии из DI-контейнера.

    Доступ к нетипизированному ``request.app.state.container``
    выполняется напрямую - Starlette не поддерживает типизацию
    ``State`` нативно, поэтому возвращаемый тип принудительно
    объявляется сигнатурой функции.

    Parameters
    ----------
    request : Request
        Объект HTTP-запроса FastAPI. Используется для доступа
        к глобальному DI-контейнеру приложения через ``app.state``.

    Returns
    -------
    LogoutCommandHandler
        Обработчик команды завершения пользовательской сессии.
    """
    return request.app.state.container.users.logout_command_handler


LogoutDependency = Annotated[LogoutCommandHandler, Depends(_get_logout_command_handler)]
"""Типизированная FastAPI-зависимость обработчика команды завершения сессии.

Инкапсулирует доступ к ``request.app.state.container`` и предоставляет
роутам готовый экземпляр :class:`LogoutCommandHandler` без ручного
приведения типов. Используется как аннотация параметра обработчика:

```python
@router.post("/logout")
async def logout(
    logout_user: LogoutDependency,
    ...,
) -> None:
    await logout_user.execute(...)
```
"""


def _get_refresh_session_command_handler(
    request: Request,
) -> RefreshSessionCommandHandler:
    """Получить обработчик команды обновления пары токенов из DI-контейнера.

    Доступ к нетипизированному ``request.app.state.container``
    выполняется напрямую - Starlette не поддерживает типизацию
    ``State`` нативно, поэтому возвращаемый тип принудительно
    объявляется сигнатурой функции.

    Parameters
    ----------
    request : Request
        Объект HTTP-запроса FastAPI. Используется для доступа
        к глобальному DI-контейнеру приложения через ``app.state``.

    Returns
    -------
    RefreshSessionCommandHandler
        Обработчик команды обновления пары токенов.
    """
    return request.app.state.container.users.refresh_session_command_handler


RefreshSessionDependency = Annotated[
    RefreshSessionCommandHandler, Depends(_get_refresh_session_command_handler)
]
"""Типизированная FastAPI-зависимость обработчика команды обновления токенов.

Инкапсулирует доступ к ``request.app.state.container`` и предоставляет
роутам готовый экземпляр :class:`RefreshSessionCommandHandler` без ручного
приведения типов. Используется как аннотация параметра обработчика:

```python
@router.post("/refresh")
async def refresh(
    refresh_session: RefreshSessionDependency,
    ...,
) -> RefreshSessionResponse:
    result = await refresh_session.execute(...)
```
"""


def _get_register_user_command_handler(
    request: Request,
) -> RegisterUserCommandHandler:
    """Получить обработчик команды регистрации пользователя из DI-контейнера.

    Доступ к нетипизированному ``request.app.state.container``
    выполняется напрямую - Starlette не поддерживает типизацию
    ``State`` нативно, поэтому возвращаемый тип принудительно
    объявляется сигнатурой функции.

    Parameters
    ----------
    request : Request
        Объект HTTP-запроса FastAPI. Используется для доступа
        к глобальному DI-контейнеру приложения через ``app.state``.

    Returns
    -------
    RegisterUserCommandHandler
        Обработчик команды регистрации нового пользователя.
    """
    return request.app.state.container.users.register_user_command_handler


RegisterUserDependency = Annotated[
    RegisterUserCommandHandler, Depends(_get_register_user_command_handler)
]
"""Типизированная FastAPI-зависимость обработчика команды регистрации.

Инкапсулирует доступ к ``request.app.state.container`` и предоставляет
роутам готовый экземпляр :class:`RegisterUserCommandHandler` без ручного
приведения типов. Используется как аннотация параметра обработчика:

```python
@router.post("/register")
async def register(
    register_user: RegisterUserDependency,
    ...,
) -> RegisterUserResponse:
    result = await register_user.execute(...)
```
"""


def _get_change_password_command_handler(
    request: Request,
) -> ChangePasswordCommandHandler:
    """Получить обработчик команды смены пароля из DI-контейнера.

    Доступ к нетипизированному ``request.app.state.container``
    выполняется напрямую - Starlette не поддерживает типизацию
    ``State`` нативно, поэтому возвращаемый тип принудительно
    объявляется сигнатурой функции.

    Parameters
    ----------
    request : Request
        Объект HTTP-запроса FastAPI. Используется для доступа
        к глобальному DI-контейнеру приложения через ``app.state``.

    Returns
    -------
    ChangePasswordCommandHandler
        Обработчик команды смены пароля пользователя.
    """
    return request.app.state.container.users.change_password_command_handler


ChangePasswordDependency = Annotated[
    ChangePasswordCommandHandler, Depends(_get_change_password_command_handler)
]
"""Типизированная FastAPI-зависимость обработчика команды смены пароля.

Инкапсулирует доступ к ``request.app.state.container`` и предоставляет
роутам готовый экземпляр :class:`ChangePasswordCommandHandler` без ручного
приведения типов. Используется как аннотация параметра обработчика:

```python
@router.post("/change-password")
async def change_password(
    change_password: ChangePasswordDependency,
    ...,
) -> None:
    await change_password.execute(...)
```
"""


def _get_auth_cookies_provider(request: Request) -> AuthCookiesProvider:
    """Получить провайдер auth-cookie из DI-контейнера.

    Доступ к нетипизированному ``request.app.state.container``
    выполняется напрямую - Starlette не поддерживает типизацию
    ``State`` нативно, поэтому возвращаемый тип принудительно
    объявляется сигнатурой функции.

    Parameters
    ----------
    request : Request
        Объект HTTP-запроса FastAPI. Используется для доступа
        к глобальному DI-контейнеру приложения через ``app.state``.

    Returns
    -------
    AuthCookiesProvider
        Провайдер установки и удаления HttpOnly-cookie refresh-токена.
    """
    return request.app.state.container.users.auth_cookies_provider


AuthCookiesProviderDependency = Annotated[
    AuthCookiesProvider, Depends(_get_auth_cookies_provider)
]
"""Типизированная FastAPI-зависимость провайдера auth-cookie.

Инкапсулирует доступ к ``request.app.state.container`` и предоставляет
роутам готовый экземпляр :class:`AuthCookiesProvider` без ручного
приведения типов. Используется как аннотация параметра обработчика:

```python
@router.post("/register")
async def register(
    response: Response,
    auth_cookies_provider: AuthCookiesProviderDependency,
    ...,
) -> RegisterUserResponse:
    auth_cookies_provider.set_refresh_token_cookie(
        response=response, refresh_token=result.refresh_token,
    )
```
"""
