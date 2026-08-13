from typing import Annotated

from fastapi import Depends, Request

from src.users.application.use_cases import LoginUseCase, RegisterUserUseCase
from src.users.presentation.http.services import AuthCookiesProvider


def _get_login_use_case(request: Request) -> LoginUseCase:
    """Получить Use Case аутентификации пользователя из DI-контейнера.

    Единственное место в модуле Users, где выполняется доступ к
    нетипизированному ``request.app.state.container`` - Starlette не
    поддерживает типизацию ``State`` нативно, поэтому возвращаемый
    тип принудительно объявляется сигнатурой функции.

    Parameters
    ----------
    request : Request
        Объект HTTP-запроса FastAPI. Используется для доступа
        к глобальному DI-контейнеру приложения через ``app.state``.

    Returns
    -------
    LoginUseCase
        Use Case аутентификации пользователя.
    """
    return request.app.state.container.users.login_use_case


LoginUserDependency = Annotated[LoginUseCase, Depends(_get_login_use_case)]
"""Типизированная FastAPI-зависимость Use Case аутентификации пользователя.

Инкапсулирует доступ к ``request.app.state.container`` и предоставляет
роутам готовый экземпляр :class:`LoginUseCase` без ручного приведения
типов. Используется как аннотация параметра обработчика:

.. code-block:: python

    @router.post("/login")
    async def login(
        login_user: LoginUserDependency,
        ...,
    ) -> LoginResponse:
        result = await login_user.execute(...)
"""


def _get_register_user_use_case(request: Request) -> RegisterUserUseCase:
    """Получить Use Case регистрации пользователя из DI-контейнера.

    Единственное место в модуле Users, где выполняется доступ к
    нетипизированному ``request.app.state.container`` - Starlette не
    поддерживает типизацию ``State`` нативно, поэтому возвращаемый
    тип принудительно объявляется сигнатурой функции.

    Parameters
    ----------
    request : Request
        Объект HTTP-запроса FastAPI. Используется для доступа
        к глобальному DI-контейнеру приложения через ``app.state``.

    Returns
    -------
    RegisterUserUseCase
        Use Case регистрации нового пользователя.
    """
    return request.app.state.container.users.register_user_use_case


RegisterUserDependency = Annotated[
    RegisterUserUseCase, Depends(_get_register_user_use_case)
]
"""Типизированная FastAPI-зависимость Use Case регистрации пользователя.

Инкапсулирует доступ к ``request.app.state.container`` и предоставляет
роутам готовый экземпляр :class:`RegisterUserUseCase` без ручного
приведения типов. Используется как аннотация параметра обработчика:

.. code-block:: python

    @router.post("/register")
    async def register(
        register_user: RegisterUserDependency,
        ...,
    ) -> RegisterUserResponse:
        result = await register_user.execute(...)
"""


def _get_auth_cookies_provider(request: Request) -> AuthCookiesProvider:
    """Получить провайдер auth-cookie из DI-контейнера.

    Единственное место в модуле Users, где выполняется доступ к
    нетипизированному ``request.app.state.container`` - Starlette не
    поддерживает типизацию ``State`` нативно, поэтому возвращаемый
    тип принудительно объявляется сигнатурой функции.

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

.. code-block:: python

    @router.post("/register")
    async def register(
        response: Response,
        auth_cookies_provider: AuthCookiesProviderDependency,
        ...,
    ) -> RegisterUserResponse:
        auth_cookies_provider.set_refresh_token_cookie(
            response=response, refresh_token=result.refresh_token,
        )
"""
